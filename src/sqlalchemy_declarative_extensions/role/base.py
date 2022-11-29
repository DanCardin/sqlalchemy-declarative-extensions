from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Generator, Iterable, List, Optional, Union

from sqlalchemy_declarative_extensions.dialects import postgresql
from sqlalchemy_declarative_extensions.role.generic import Role

R = Union[postgresql.Role, Role]
R_unknown = Union[postgresql.Role, Role, str]


@dataclass
class Roles:
    roles: List[R] = field(default_factory=list)
    ignore_unspecified: bool = False
    ignore_roles: List[str] = field(default_factory=list)

    @classmethod
    def coerce_from_unknown(
        cls, unknown: Union[None, Iterable[R_unknown], Roles]
    ) -> Optional[Roles]:
        if isinstance(unknown, Roles):
            return unknown

        if isinstance(unknown, Iterable):
            return Roles().are(*unknown)

        return None

    def __iter__(self) -> Generator[R, None, None]:
        for role in self.roles:
            yield role

    def are(self, *roles: R_unknown):
        return replace(
            self,
            roles=[Role.coerce_from_unknown(role) for role in roles],
        )
