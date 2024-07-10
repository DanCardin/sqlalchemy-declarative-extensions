from __future__ import annotations

import typing
from dataclasses import dataclass, field

if typing.TYPE_CHECKING:
    from sqlalchemy_declarative_extensions.role import Role


@dataclass
class Context:
    roles: list[Role] = field(default_factory=list)

    def enter_role(self, role):
        self.roles.append(role)

    def exit_role(self):
        self.roles.pop()

    @property
    def role(self) -> Role | None:
        if not self.roles:
            return None
        return self.roles[-1]


context = Context()
