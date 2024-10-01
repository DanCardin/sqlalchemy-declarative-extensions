from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Iterable, Sequence

from sqlalchemy import MetaData
from sqlalchemy.sql.base import Executable
from sqlalchemy.sql.ddl import CreateSchema, DropSchema
from typing_extensions import Self

from sqlalchemy_declarative_extensions.context import context

if TYPE_CHECKING:
    from sqlalchemy_declarative_extensions.role import Role


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

        >>> schemas = Schemas(ignore_unspecified=True)

        - With some actual schemas

        >>> from sqlalchemy_declarative_extensions import Schema, Schemas
        >>> schema = Schemas().are("foo", Schema("bar"), ...)
    """

    schemas: Sequence[Schema] = ()
    ignore_unspecified: bool = False

    @classmethod
    def coerce_from_unknown(
        cls, unknown: None | Iterable[Schema | str] | Schemas
    ) -> Schemas | None:
        if isinstance(unknown, Schemas):
            return unknown

        if isinstance(unknown, Iterable):
            return cls().are(*unknown)

        return None

    @classmethod
    def extract(cls, metadata: MetaData | list[MetaData | None] | None) -> Self | None:
        if not isinstance(metadata, Sequence):
            metadata = [metadata]

        instances: list[Self] = [
            m.info["schemas"] for m in metadata if m and m.info.get("schemas")
        ]

        instance_count = len(instances)
        if instance_count == 0:
            return None

        if instance_count == 1:
            return instances[0]

        if not all(
            x.ignore_unspecified == instances[0].ignore_unspecified for x in instances
        ):
            raise ValueError(
                "All combined `Schemas` instances must agree on the set of settings: ignore_unspecified"
            )

        schemas = tuple(s for instance in instances for s in instance.schemas)
        ignore_unspecified = instances[0].ignore_unspecified
        return cls(schemas=schemas, ignore_unspecified=ignore_unspecified)

    def __iter__(self):
        yield from self.schemas

    def are(self, *schemas: Schema | str):
        """Declare the set of schemas which should exist."""
        return replace(
            self,
            schemas=tuple([Schema.coerce_from_unknown(schema) for schema in schemas]),
        )


@dataclass(order=True)
class Schema:
    """Represents a schema."""

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

    def to_sql_create(self) -> Executable | str:
        return CreateSchema(self.name)

    def to_sql_drop(self) -> Executable | str:
        return DropSchema(self.name)
