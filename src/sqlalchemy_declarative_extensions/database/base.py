from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Iterable, Sequence

from typing_extensions import Self

from sqlalchemy_declarative_extensions.context import context

if TYPE_CHECKING:
    from sqlalchemy_declarative_extensions.role import Role


@dataclass(frozen=True)
class Databases:
    """A collection of databases and the settings for diff/collection.

    Arguments:
        databases: The list of grants
        ignore_unspecified: Optionally ignore detected grants which do not match
            the set of defined grants.

    Examples:
        - No databases

        >>> databases = Databases()

        - Some options set

        >>> databases = Databases(ignore_unspecified=True)

        - With some actual databases

        >>> from sqlalchemy_declarative_extensions import Database, Databases
        >>> database = Databases().are("foo", Database("bar"), ...)
    """

    databases: Sequence[Database] = ()
    ignore_unspecified: bool = False

    @classmethod
    def coerce_from_unknown(
        cls, unknown: None | Iterable[Database | str] | Databases
    ) -> Databases | None:
        if isinstance(unknown, Databases):
            return unknown

        if isinstance(unknown, Iterable):
            return cls().are(*unknown)

        return None

    def __iter__(self):
        yield from self.databases

    def are(self, *databases: Database | str):
        """Declare the set of databases which should exist."""
        return replace(
            self,
            databases=tuple(
                [Database.coerce_from_unknown(database) for database in databases]
            ),
        )


@dataclass(order=True)
class Database:
    """Represents a database."""

    name: str

    use_role: Role | str | None = None

    def __post_init__(self):
        if not self.use_role:
            self.use_role = context.role

    @classmethod
    def coerce_from_unknown(cls, unknown: Self | str) -> Self:
        if isinstance(unknown, cls):
            return unknown

        return cls(unknown)  # type: ignore

    def to_sql_create(self) -> str:
        return f"CREATE DATABASE {self.name}"

    def to_sql_drop(self) -> str:
        return f"DROP DATABASE {self.name}"
