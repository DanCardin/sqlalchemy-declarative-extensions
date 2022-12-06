from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions.dialects import get_role_cls, get_roles
from sqlalchemy_declarative_extensions.role.base import Roles
from sqlalchemy_declarative_extensions.role.generic import Role
from sqlalchemy_declarative_extensions.role.topological_sort import topological_sort


class RoleOp:
    pass


@dataclass
class CreateRoleOp(RoleOp):
    role: Role

    @classmethod
    def create_role(cls, operations, role_name: str, **options):
        assert operations.migration_context.connection
        role_cls = get_role_cls(operations.migration_context.connection)
        role = role_cls(role_name, **options)
        op = cls(role)
        return operations.invoke(op)

    def reverse(self):
        return DropRoleOp(self.role)

    def to_sql(self):
        return self.role.to_sql_create()


@dataclass
class UpdateRoleOp(RoleOp):
    from_role: Role
    to_role: Role

    @classmethod
    def update_role(
        cls, operations, role_name: str, *, from_options=None, **to_options
    ):
        assert operations.migration_context.connection
        role_cls = get_role_cls(operations.migration_context.connection)

        from_role = role_cls(role_name, **(from_options or {}))
        to_role = role_cls(role_name, **to_options)
        op = cls(from_role, to_role)
        return operations.invoke(op)

    def reverse(self):
        return UpdateRoleOp(from_role=self.to_role, to_role=self.from_role)

    def to_sql(self):
        return self.from_role.to_sql_update(self.to_role)


@dataclass
class DropRoleOp(RoleOp):
    role: Role

    @classmethod
    def drop_role(cls, operations, role_name: str):
        op = cls(Role(role_name))
        return operations.invoke(op)

    def reverse(self):
        return CreateRoleOp(self.role)

    def to_sql(self):
        return self.role.to_sql_drop()


Operation = Union[CreateRoleOp, UpdateRoleOp, DropRoleOp]


def compare_roles(connection: Connection, roles: Roles) -> list[Operation]:
    result: list[Operation] = []
    if not roles:
        return result

    roles_by_name = {r.name: r for r in roles.roles}
    expected_role_names = set(roles_by_name)

    existing_roles = get_roles(connection)
    existing_roles_by_name = {r.name: r for r in existing_roles}
    existing_role_names = set(existing_roles_by_name)

    new_role_names = expected_role_names - existing_role_names
    removed_role_names = existing_role_names - expected_role_names

    role_cls = get_role_cls(connection)

    for role in topological_sort(roles.roles):
        role_name = role.name

        if role_name in roles.ignore_roles:
            continue

        role_created = role_name in new_role_names

        if role_created:
            result.append(CreateRoleOp(role))
        else:
            existing_role = existing_roles_by_name[role_name]
            role_cls = type(existing_role)

            # An input role might be defined as a more general `Role` while
            # the `existing_role` will always be a concrete dialect-specific version.
            concrete_defined_role = role_cls.from_unknown_role(role)

            role_updated = existing_role != concrete_defined_role
            if role_updated:
                existing_role = existing_roles_by_name[role_name]
                result.append(
                    UpdateRoleOp(
                        from_role=existing_role,
                        to_role=role_cls.from_unknown_role(role),
                    )
                )

    if not roles.ignore_unspecified:
        for removed_role in removed_role_names:
            if removed_role in roles.ignore_roles:
                continue
            result.append(DropRoleOp(role_cls(removed_role)))

    return result
