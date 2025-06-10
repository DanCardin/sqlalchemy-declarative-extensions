from __future__ import annotations

from dataclasses import dataclass, field
from typing import Union

from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions.dialects import get_role_cls, get_roles
from sqlalchemy_declarative_extensions.op import ExecuteOp
from sqlalchemy_declarative_extensions.role.base import Roles
from sqlalchemy_declarative_extensions.role.generic import Role
from sqlalchemy_declarative_extensions.role.state import RoleState
from sqlalchemy_declarative_extensions.role.topological_sort import topological_sort


@dataclass
class RoleOp(ExecuteOp):
    pass


@dataclass
class CreateRoleOp(RoleOp):
    role: Role
    use_role_ops: list[UseRoleOp] = field(default_factory=list)

    @classmethod
    def create_role(cls, operations, role_name: str, **options):
        assert operations.migration_context.connection
        role_cls = get_role_cls(operations.migration_context.connection)
        role = role_cls(role_name, **options)
        op = cls(role)
        return operations.invoke(op)

    def reverse(self):
        return DropRoleOp(self.role)

    def to_sql(self, raw: bool = True) -> list[str]:
        role_sql = UseRoleOp.to_sql_from_use_role_ops(self.use_role_ops)
        return [*role_sql, *self.role.to_sql_create(raw=raw)]


@dataclass
class UpdateRoleOp(RoleOp):
    from_role: Role
    role: Role
    use_role_ops: list[UseRoleOp] = field(default_factory=list)

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
        return UpdateRoleOp(from_role=self.role, role=self.from_role)

    def to_sql(self, raw: bool = True):
        role_sql = UseRoleOp.to_sql_from_use_role_ops(self.use_role_ops)
        return [*role_sql, *self.from_role.to_sql_update(self.role, raw=raw)]


@dataclass
class DropRoleOp(RoleOp):
    role: Role
    use_role_ops: list[UseRoleOp] = field(default_factory=list)

    @classmethod
    def drop_role(cls, operations, role_name: str):
        op = cls(Role(role_name))
        return operations.invoke(op)

    def reverse(self):
        return CreateRoleOp(self.role)

    def to_sql(self, raw: bool = True) -> list[str]:
        role_sql = UseRoleOp.to_sql_from_use_role_ops(self.use_role_ops)
        return [*role_sql, *self.role.to_sql_drop(raw=raw)]


@dataclass
class UseRoleOp(RoleOp):
    role: Role
    undo: bool = False

    @classmethod
    def use_role(cls, operations, role_name: str):
        op = cls(Role(role_name))
        return operations.invoke(op)

    @classmethod
    def to_sql_from_use_role_ops(cls, use_role_ops: list[UseRoleOp] | None):
        return (
            [statement for role_op in use_role_ops for statement in role_op.to_sql()]
            if use_role_ops
            else []
        )

    def reverse(self):
        return self

    def to_sql(self, raw: bool = True) -> list[str]:
        return self.role.to_sql_use(undo=self.undo)


Operation = Union[CreateRoleOp, UpdateRoleOp, DropRoleOp, UseRoleOp]


def compare_roles(connection: Connection, roles: Roles) -> list[Operation]:
    result: list[Operation] = []
    if not roles:
        return result

    roles_by_name = {r.name: r for r in roles.roles if not r.external}
    expected_role_names = set(roles_by_name)

    existing_roles = get_roles(connection)
    existing_roles_by_name = {r.name: r for r in existing_roles}
    existing_role_names = set(existing_roles_by_name)

    new_role_names = expected_role_names - existing_role_names
    removed_role_names = existing_role_names - expected_role_names

    role_cls: type[Role] = get_role_cls(connection)

    role_state = RoleState(role_cls)

    for role in topological_sort(roles.roles):
        role_name = role.name

        if role_name in roles.ignore_roles or role.external:
            continue

        role_created = role_name in new_role_names

        # An input role might be defined as a more general `Role` while
        # the `existing_role` will always be a concrete dialect-specific version.
        concrete_defined_role: Role = role_cls.from_unknown_role(role).normalize()

        use_role_ops = role_state.use_role(concrete_defined_role.use_role)

        if role_created:
            result.append(
                CreateRoleOp(concrete_defined_role, use_role_ops=use_role_ops)
            )
        else:
            existing_role = existing_roles_by_name[role_name].normalize()
            role_cls = type(existing_role)

            role_updated = existing_role != concrete_defined_role
            if role_updated:
                existing_role = existing_roles_by_name[role_name]
                result.append(
                    UpdateRoleOp(
                        from_role=existing_role,
                        role=concrete_defined_role,
                        use_role_ops=use_role_ops,
                    )
                )

    if not roles.ignore_unspecified:
        for removed_role in removed_role_names:
            if removed_role in roles.ignore_roles:
                continue

            # TODO: Perhaps we could record the owner upstream, and use that to imply a UseRoleOp here?
            result.append(DropRoleOp(role_cls(removed_role)))

    result.extend(role_state.reset())

    return result
