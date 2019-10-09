from __future__ import annotations

from dataclasses import dataclass
from typing import List, Union

from sqlalchemy import text
from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions.role.base import PGRole, Roles
from sqlalchemy_declarative_extensions.role.topological_sort import topological_sort
from sqlalchemy_declarative_extensions.sqlalchemy import dialect_dispatch


class RoleOp:
    pass


@dataclass
class CreateRoleOp(RoleOp):
    role: PGRole

    @classmethod
    def create_role(cls, operations, role, **options):
        op = cls(PGRole(role, **options))
        return operations.invoke(op)

    def reverse(self):
        return DropRoleOp(self.role)


@dataclass
class UpdateRoleOp(RoleOp):
    from_role: PGRole
    to_role: PGRole

    @classmethod
    def update_role(cls, operations, from_role: PGRole, to_role: PGRole):
        op = cls(from_role, to_role)
        return operations.invoke(op)

    def reverse(self):
        return UpdateRoleOp(from_role=self.to_role, to_role=self.from_role)


@dataclass
class DropRoleOp(RoleOp):
    role: PGRole

    @classmethod
    def drop_role(cls, operations, role):
        op = cls(PGRole(role))
        return operations.invoke(op)

    def reverse(self):
        return CreateRoleOp(self.role)


Operation = Union[CreateRoleOp, UpdateRoleOp, DropRoleOp]


def compare_roles(connection: Connection, roles: Roles) -> List[Operation]:
    result: List[Operation] = []
    if not roles:
        return result

    roles_by_name = {r.name: r for r in roles.roles}
    expected_role_names = set(roles_by_name)

    existing_roles = get_existing_roles(connection)
    existing_roles_by_name = {r.name: r for r in existing_roles}
    existing_role_names = set(existing_roles_by_name)

    new_role_names = expected_role_names - existing_role_names
    removed_role_names = existing_role_names - expected_role_names

    for role in topological_sort(roles.roles):
        role_name = role.name

        if role_name in roles.ignore_roles:
            continue

        role_created = role_name in new_role_names

        if role_created:
            result.append(CreateRoleOp(role))
        else:
            existing_role = existing_roles_by_name[role_name]
            role_updated = existing_role != role
            if role_updated:
                existing_role = existing_roles_by_name[role_name]
                result.append(UpdateRoleOp(from_role=existing_role, to_role=role))

    if not roles.ignore_unspecified:
        for removed_role in removed_role_names:
            if removed_role in roles.ignore_roles:
                continue
            result.append(DropRoleOp(PGRole(removed_role)))

    return result


def get_existing_roles_postgresql(connection: Connection, exclude=None):
    select_roles = text(
        """
        SELECT r.rolname, r.rolsuper, r.rolinherit,
          r.rolcreaterole, r.rolcreatedb, r.rolcanlogin,
          r.rolconnlimit, r.rolvaliduntil,
          ARRAY(SELECT b.rolname
                FROM pg_catalog.pg_auth_members m
                JOIN pg_catalog.pg_roles b ON (m.roleid = b.oid)
                WHERE m.member = r.oid) as memberof
        , r.rolreplication
        , r.rolbypassrls
        FROM pg_catalog.pg_roles r
        WHERE r.rolname !~ '^pg_'
        ORDER BY 1;
        """
    )
    result = [
        PGRole.from_pg_role(r)
        for r in connection.execute(select_roles).fetchall()
        if not r.rolname.startswith("pg_")
    ]
    if exclude:
        result = [role for role in result if role.name not in exclude]
    return result


get_existing_roles = dialect_dispatch(
    postgresql=get_existing_roles_postgresql,
)
