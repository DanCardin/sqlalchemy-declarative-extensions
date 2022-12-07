from __future__ import annotations

from dataclasses import dataclass
from itertools import groupby
from typing import Container, Union

from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions.dialects import (
    get_default_grants,
    get_grants,
    get_objects,
)
from sqlalchemy_declarative_extensions.dialects.postgresql import (
    DefaultGrantStatement,
    GrantStatement,
    GrantTypes,
)
from sqlalchemy_declarative_extensions.grant.base import Grants
from sqlalchemy_declarative_extensions.role.base import Roles


@dataclass
class GrantPrivilegesOp:
    grant: DefaultGrantStatement | GrantStatement

    def reverse(self):
        return RevokePrivilegesOp(self.grant)

    def to_sql(self):
        return self.grant.to_sql()


@dataclass
class RevokePrivilegesOp:
    grant: DefaultGrantStatement | GrantStatement

    def reverse(self):
        return GrantPrivilegesOp(self.grant)

    def to_sql(self):
        return self.grant.invert().to_sql()


Operation = Union[GrantPrivilegesOp, RevokePrivilegesOp]


def compare_grants(
    connection: Connection, grants: Grants, roles: Roles | None = None
) -> list[Operation]:
    result: list[Operation] = []

    current_role: str = connection.engine.url.username  # type: ignore

    filtered_roles: set[str] | None = None
    if grants.only_defined_roles:
        filtered_roles = {r.name for r in (roles or [])}

    default_grant_ops = compare_default_grants(connection, grants, roles=filtered_roles)
    result.extend(default_grant_ops)

    if grants.default_grants_imply_grants:
        grant_ops = compare_object_grants(
            connection, grants, username=current_role, roles=filtered_roles
        )
        result.extend(grant_ops)

    return result


def compare_default_grants(
    connection: Connection,
    grants: Grants,
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

    if not grants.ignore_unspecified:
        for grant in DefaultGrantStatement.combine(list(extra_grants)):
            result.append(RevokePrivilegesOp(grant))

    for grant in DefaultGrantStatement.combine(list(missing_grants)):
        result.append(GrantPrivilegesOp(grant))

    return result


def compare_object_grants(
    connection: Connection,
    grants: Grants,
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

        for schema in grant.default_grant.in_schemas:
            existing_tables_in_schema = existing_tables_by_schema.get(schema)
            if not existing_tables_in_schema:
                continue

            for _, table, relkind in existing_tables_in_schema:
                object_type = GrantTypes.from_relkind(relkind)

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

    if not grants.ignore_unspecified:
        for grant in GrantStatement.combine(list(extra_grants)):
            result.append(RevokePrivilegesOp(grant))

    for grant in GrantStatement.combine(list(missing_grants)):
        result.append(GrantPrivilegesOp(grant))

    return result
