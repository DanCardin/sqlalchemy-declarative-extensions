from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Generic, Iterable, List, Optional, TypeVar, Union

from sqlalchemy_declarative_extensions.grant import postgresql
from sqlalchemy_declarative_extensions.schema.base import Schema

G = TypeVar("G", postgresql.DefaultGrantStatement, postgresql.GrantStatement)


@dataclass
class Grants(Generic[G]):
    """A collection of grants and the settings for diff/collection.

    Arguments:
        grants: The list of grants
        ignore_unspecified: Optionally ignore detected grants which do not match
            the set of defined grants.
        ignore_grants_in: Optionally ignore grants in a particular set of schemas.

    Examples:
        - No grants

        >>> grants = Grants()

        - Some options set

        >>> grants = Grants().options(ignore_unspecified=True)

        - With some actual grants

        >>> from sqlalchemy_declarative_extensions import PGGrant
        >>> grants = Grants().are(PGGrant(...), PGGrant(...), ...)

    Note, the "benefit" of using the above fluent interface is that it coerces obvious
    substitutes for the types required by a `Grant`, for example `ignore_grants_in` is
    a `List[Schema]`, but the string name of a schema can be used to produce that object.
    If that's not meaningful to you, then using the direct constructor can work
    equally well.
    """

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
