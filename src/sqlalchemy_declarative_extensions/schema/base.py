from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable, Optional, Sequence, Union


@dataclass(frozen=True)
class Schemas:
    """A collection of schemas and the settings for diff/collection.

    Arguments:
        schemas: The list of grants
        ignore_unspecified: Optionally ignore detected grants which do not match
            the set of defined grants.

    Examples:
        - No schemas

        >>> schemas = Schemas()

        - Some options set

        >>> schemas = Schemas().options(ignore_unspecified=True)

        - With some actual schemas

        >>> from sqlalchemy_declarative_extensions import Schema, Schemas
        >>> schema = Schemas().are("foo", Schema("bar"), ...)

    Note, the "benefit" of using the above fluent interface is that it coerces obvious
    substitutes for the types required by a `Schemas`, for example `ignore_unspecified` is
    a `Sequence[Schema]`, but the string name of a schema can be used to produce that object.
    If that's not meaningful to you, then using the direct constructor can work
    equally well.
    """

    schemas: Sequence[Schema] = ()
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
        """Declare the set of schemas which should exist."""
        result = replace(
            self,
            schemas=tuple([Schema.coerce_from_unknown(schema) for schema in schemas]),
        )
        return result


@dataclass(frozen=True, order=True)
class Schema:
    """Represents a schema."""

    name: str

    @classmethod
    def coerce_from_unknown(cls, unknown: Union[Schema, str]) -> Schema:
        if isinstance(unknown, Schema):
            return unknown

        return cls(unknown)
