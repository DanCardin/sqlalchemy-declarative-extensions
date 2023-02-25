from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Generator, Iterable

from sqlalchemy_declarative_extensions.dialects import postgresql
from sqlalchemy_declarative_extensions.role import generic


@dataclass
class Roles:
    roles: list[postgresql.Role | generic.Role] = field(default_factory=list)
    ignore_unspecified: bool = False
    ignore_roles: list[str] = field(default_factory=list)

    @classmethod
    def coerce_from_unknown(
        cls,
        unknown: None | Iterable[postgresql.Role | generic.Role | str] | Roles,
    ) -> Roles | None:
        if isinstance(unknown, Roles):
            return unknown

        if isinstance(unknown, Iterable):
            return Roles().are(*unknown)

        return None

    def __iter__(self) -> Generator[postgresql.Role | generic.Role, None, None]:
        yield from self.roles

    def are(self, *roles: postgresql.Role | generic.Role | str):
        return replace(
            self,
            roles=[generic.Role.coerce_from_unknown(role) for role in roles],
        )
