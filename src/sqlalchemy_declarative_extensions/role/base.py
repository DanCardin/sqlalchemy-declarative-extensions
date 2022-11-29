from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Generator, Iterable, List, Optional, Union

from sqlalchemy_declarative_extensions.dialects import postgresql
from sqlalchemy_declarative_extensions.role import generic


@dataclass
class Roles:
    roles: List[Union[postgresql.Role, generic.Role]] = field(default_factory=list)
    ignore_unspecified: bool = False
    ignore_roles: List[str] = field(default_factory=list)

    @classmethod
    def coerce_from_unknown(
        cls,
        unknown: Union[
            None, Iterable[Union[postgresql.Role, generic.Role, str]], Roles
        ],
    ) -> Optional[Roles]:
        if isinstance(unknown, Roles):
            return unknown

        if isinstance(unknown, Iterable):
            return Roles().are(*unknown)

        return None

    def __iter__(self) -> Generator[Union[postgresql.Role, generic.Role], None, None]:
        for role in self.roles:
            yield role

    def are(self, *roles: Union[postgresql.Role, generic.Role, str]):
        return replace(
            self,
            roles=[generic.Role.coerce_from_unknown(role) for role in roles],
        )
