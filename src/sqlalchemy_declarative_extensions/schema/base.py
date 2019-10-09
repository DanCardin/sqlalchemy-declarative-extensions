from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable, Optional, Tuple, Union


@dataclass(frozen=True)
class Schemas:
    schemas: Tuple[Schema, ...] = ()
    ignore_unspecified: bool = False

    @classmethod
    def coerce_from_unknown(
        cls, unknown: Union[None, Iterable[Union[Schema, str]], Schemas]
    ) -> Optional[Schemas]:
        if isinstance(unknown, Schemas):
            return unknown

        if isinstance(unknown, Iterable):
            return cls().are(*unknown)

        return None

    @classmethod
    def options(cls, ignore_unspecified=False):
        return cls(ignore_unspecified=ignore_unspecified)

    def __iter__(self):
        for schema in self.schemas:
            yield schema

    def are(self, *schemas: Union[Schema, str]):
        result = replace(
            self,
            schemas=tuple([Schema.coerce_from_unknown(schema) for schema in schemas]),
        )
        return result


@dataclass(frozen=True, order=True)
class Schema:
    name: str

    @classmethod
    def coerce_from_unknown(cls, unknown: Union[Schema, str]) -> Schema:
        if isinstance(unknown, Schema):
            return unknown

        return cls(unknown)
