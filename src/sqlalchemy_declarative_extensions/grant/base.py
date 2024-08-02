from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Generic, Iterable, Sequence, TypeVar, Union

from typing_extensions import Self

from sqlalchemy_declarative_extensions.sql import HasName, coerce_name, split_schema


@dataclass
class Grants:
    """A collection of grants and the settings for diff/collection.

    Arguments:
        grants: The list of grants
        ignore_unspecified: Defaults to `False`. When `True`, ignore detected grants
            which do not match the set of defined grants.
        ignore_self_grants: Defaults to `True`. When `True`, ignores grants to the
            current user. It's typical in migrations that the a single user performs
            migrations and will have implicitly granted grants on all objects. In this
            scenario, it can be tedious to define those permissions on every object,
            so they are ignored by default.
        only_defined_roles: Defaults to `True`. When `True`, only applies to roles
            specified in the `roles` section.
        default_grants_imply_grants: Defaults to `True`. When `True`, default grants
            also imply the set of expected actual grants. This allows one to specify
            only default grants, and per-object grants will be made to match the
            default set.

    Examples:
        - No grants

        >>> grants = Grants()

        - Some options set

        >>> grants = Grants(ignore_unspecified=True)

        - With some actual grants

        >>> from sqlalchemy_declarative_extensions.dialects.postgresql import DefaultGrant
        >>> grants = Grants().are(DefaultGrant(..., ...), ...)
    """

    grants: list[G] = field(default_factory=list)

    ignore_unspecified: bool = False
    ignore_self_grants: bool = True
    only_defined_roles: bool = True
    default_grants_imply_grants: bool = True

    @classmethod
    def coerce_from_unknown(cls, unknown: None | Iterable[G] | Grants) -> Grants | None:
        if isinstance(unknown, Grants):
            return unknown

        if isinstance(unknown, Iterable):
            return Grants().are(*unknown)

        return None

    def __iter__(self):
        yield from self.grants

    def are(self, *grants: G):
        return replace(self, grants=list(grants))


Grant = TypeVar("Grant")
DefaultGrant = TypeVar("DefaultGrant")
GrantType = TypeVar("GrantType")


@dataclass(frozen=True)
class DefaultGrantStatement(Generic[DefaultGrant, Grant]):
    default_grant: DefaultGrant
    grant: Grant

    def invert(self) -> Self:
        raise NotImplementedError()

    def to_sql(self) -> list[str]:
        raise NotImplementedError()

    def explode(self) -> list[Self]:
        raise NotImplementedError()

    @classmethod
    def combine(cls, grants: Sequence[Self]) -> list[Self]:
        raise NotImplementedError()


@dataclass(frozen=True)
class GrantStatement(Generic[Grant, GrantType]):
    grant: Grant
    grant_type: GrantType

    def invert(self) -> Self:
        raise NotImplementedError()

    def to_sql(self) -> list[str]:
        raise NotImplementedError()

    def explode(self) -> list[Self]:
        raise NotImplementedError()

    @classmethod
    def combine(cls, grants: Sequence[Self]) -> list[Self]:
        raise NotImplementedError()


def render_grant_or_revoke(revoke: bool) -> str:
    return "REVOKE" if revoke else "GRANT"


def render_to_or_from(revoke: bool, target_role: str) -> str:
    return f'FROM "{target_role}"' if revoke else f'TO "{target_role}"'


def quote_table_name(name: str):
    schema, name = split_schema(name)

    if schema:
        return f'"{schema}"."{name}"'
    return f'"{name}"'


def render_grant_option(grant_option: bool) -> str | None:
    if grant_option:
        return "WITH GRANT OPTION"
    return None


def map_schema_names(*schemas: str | HasName):
    return sorted([coerce_name(s) for s in schemas])


G = Union[DefaultGrantStatement, GrantStatement]
