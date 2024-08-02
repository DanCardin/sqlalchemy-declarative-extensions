from __future__ import annotations

from dataclasses import dataclass
from itertools import groupby
from typing import Container, Union

from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions.dialects import (
    get_default_grant_cls,
    get_default_grants,
    get_grant_cls,
    get_grants,
    get_objects,
    get_role_cls,
)

# GrantTypes,
from sqlalchemy_declarative_extensions.grant.base import (
    DefaultGrantStatement,
    Grants,
    GrantStatement,
)
from sqlalchemy_declarative_extensions.role.base import Roles
from sqlalchemy_declarative_extensions.role.compare import UseRoleOp
from sqlalchemy_declarative_extensions.role.state import RoleState


@dataclass
class GrantPrivilegesOp:
    grant: DefaultGrantStatement | GrantStatement

    def reverse(self):
        return RevokePrivilegesOp(self.grant)

    def to_sql(self) -> list[str]:
        return self.grant.to_sql()


@dataclass
class RevokePrivilegesOp:
    grant: DefaultGrantStatement | GrantStatement

    def reverse(self):
        return GrantPrivilegesOp(self.grant)

    def to_sql(self) -> list[str]:
        return self.grant.invert().to_sql()


Operation = Union[GrantPrivilegesOp, RevokePrivilegesOp, UseRoleOp]


def compare_grants(
    connection: Connection, grants: Grants, roles: Roles | None = None
) -> list[Operation]:
    result: list[Operation] = []

    assert connection.engine.url.username
    current_role: str = connection.engine.url.username

    filtered_roles: set[str] | None = None
    if grants.only_defined_roles:
        filtered_roles = {r.name for r in (roles or [])}

    role_cls = get_role_cls(connection)
    role_state = RoleState(role_cls)

    default_grant_ops = compare_default_grants(
        connection, grants, role_state, roles=filtered_roles
    )
    result.extend(default_grant_ops)

    if grants.default_grants_imply_grants:
        grant_ops = compare_object_grants(
            connection,
            grants,
            role_state=role_state,
            username=current_role,
            roles=filtered_roles,
        )
        result.extend(grant_ops)

    result.extend(role_state.reset())

    return result


def compare_default_grants(
    connection: Connection,
    grants: Grants,
    role_state: RoleState,
    roles: Container[str] | None = None,
):
    result: list[Operation] = []

    existing_default_grants = get_default_grants(connection, roles=roles, expanded=True)

    expected_grants = []
    for grant in grants:
        if not isinstance(grant, DefaultGrantStatement):
            continue

        expected_grants.extend(grant.explode())

    missing_grants = set(expected_grants) - set(existing_default_grants)
    extra_grants = set(existing_default_grants) - set(expected_grants)

    default_grant_cls: type[DefaultGrantStatement] = get_default_grant_cls(connection)

    if not grants.ignore_unspecified:
        for grant in default_grant_cls.combine(list(extra_grants)):
            result.extend(role_state.use_role(grant.use_role))
            result.append(RevokePrivilegesOp(grant))

    for grant in default_grant_cls.combine(list(missing_grants)):
        result.extend(role_state.use_role(grant.use_role))
        result.append(GrantPrivilegesOp(grant))

    return result


def compare_object_grants(
    connection: Connection,
    grants: Grants,
    role_state: RoleState,
    username: str,
    roles: Container[str] | None = None,
):
    result: list[Operation] = []

    expected_grants = [
        sub_g
        for grant in grants
        for sub_g in grant.explode()
        if isinstance(sub_g, GrantStatement)
    ]

    existing_tables = get_objects(connection)
    existing_tables_by_schema = {
        s: list(g) for s, g in groupby(existing_tables, lambda r: r[0])
    }
    for grant in grants:
        if not isinstance(grant, DefaultGrantStatement):
            continue

        grant_type = grant.default_grant.grant_type.to_grant_type()
        grant_types_cls = grant_type.__class__

        for schema in grant.default_grant.in_schemas:
            existing_tables_in_schema = existing_tables_by_schema.get(schema)
            if not existing_tables_in_schema:
                continue

            for _, table, relkind in existing_tables_in_schema:
                object_type = grant_types_cls.from_relkind(relkind)

                if object_type == grant_type:
                    expected_grants.extend(
                        grant.grant.on_objects(table, object_type=object_type).explode()
                    )

    existing_grants = get_grants(connection, roles=roles, expanded=True)

    if grants.ignore_self_grants:
        existing_grants = [
            g for g in existing_grants if g.grant.target_role != username
        ]

    missing_grants = set(expected_grants) - set(existing_grants)
    extra_grants = set(existing_grants) - set(expected_grants)

    grant_cls: type[GrantStatement] = get_grant_cls(connection)

    if not grants.ignore_unspecified:
        for grant in grant_cls.combine(list(extra_grants)):
            result.extend(role_state.use_role(grant.use_role))
            result.append(RevokePrivilegesOp(grant))

    for grant in grant_cls.combine(list(missing_grants)):
        result.extend(role_state.use_role(grant.use_role))
        result.append(GrantPrivilegesOp(grant))

    return result
