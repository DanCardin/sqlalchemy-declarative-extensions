from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Generic, Iterable, List, Optional, TypeVar, Union

from sqlalchemy_declarative_extensions.grant import postgresql
from sqlalchemy_declarative_extensions.schema.base import Schema

G = TypeVar("G", postgresql.DefaultGrantStatement, postgresql.GrantStatement)


@dataclass
class Grants(Generic[G]):
    grants: List[G] = field(default_factory=list)
    ignore_unspecified: bool = False
    ignore_grants_in: Optional[List[Schema]] = None

    @classmethod
    def coerce_from_unknown(
        cls, unknown: Union[None, Iterable[G], Grants]
    ) -> Optional[Grants]:
        if isinstance(unknown, Grants):
            return unknown

        if isinstance(unknown, Iterable):
            return Grants().are(*unknown)

        return None

    @classmethod
    def options(
        cls,
        *,
        ignore_unspecified: bool = False,
        ignore_grants_in: Optional[List[Union[str, Schema]]] = None,
    ):
        return cls(
            ignore_unspecified=ignore_unspecified,
            ignore_grants_in=[Schema.coerce_from_unknown(s) for s in ignore_grants_in]
            if ignore_grants_in
            else None,
        )

    def __iter__(self):
        for grant in self.grants:
            yield grant

    def are(self, *grants: Iterable[G]):
        return replace(self, grants=list(grants))
