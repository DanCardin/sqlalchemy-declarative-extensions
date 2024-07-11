from __future__ import annotations

import typing
from dataclasses import dataclass

from sqlalchemy.engine.base import Connection
from typing_extensions import Self

from sqlalchemy_declarative_extensions.dialects import get_role_cls
from sqlalchemy_declarative_extensions.sql import coerce_name

if typing.TYPE_CHECKING:
    from sqlalchemy_declarative_extensions.role import Role
    from sqlalchemy_declarative_extensions.role.compare import UseRoleOp


@dataclass
class RoleState:
    role_cls: type[Role]
    current_role: str | None = None

    @classmethod
    def from_connection(cls, connection: Connection) -> Self:
        role_cls = get_role_cls(connection)
        return cls(role_cls)

    def use_role(self, role: Role | str | None) -> list[UseRoleOp]:
        from sqlalchemy_declarative_extensions.role.compare import UseRoleOp

        result = []

        new_role = coerce_name(role) if role is not None else None
        if self.current_role != new_role:
            if self.current_role:
                op = UseRoleOp(self.role_cls(""), undo=True)
                result.append(op)

            if new_role:
                new_role_instance = self.role_cls(new_role)
                op = UseRoleOp(new_role_instance)
                self.current_role = new_role
                result.append(op)

        return result

    def reset(self) -> list[UseRoleOp]:
        from sqlalchemy_declarative_extensions.role.compare import UseRoleOp

        result = []
        if self.current_role:
            result.append(UseRoleOp(self.role_cls(self.current_role), undo=True))
        return result
