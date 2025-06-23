from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Iterable, Sequence

from sqlalchemy import MetaData
from typing_extensions import Self

from sqlalchemy_declarative_extensions.sql import qualify_name, quote_name
from sqlalchemy_declarative_extensions.sqlalchemy import HasMetaData


@dataclass
class Procedure:
    """Describes a user defined procedure.

    Many procedure attributes are not currently supported. Support is **currently**
    minimal due to being a means to an end for defining triggers.
    """

    name: str
    definition: str
    language: str = "sql"
    schema: str | None = None

    @classmethod
    def from_unknown_procedure(cls, f: Procedure) -> Self:
        if isinstance(f, cls):
            return f

        return cls(
            name=f.name,
            definition=f.definition,
            language=f.language,
            schema=f.schema,
        )

    @property
    def qualified_name(self):
        return qualify_name(self.schema, self.name)

    def normalize(self) -> Self:
        raise NotImplementedError()  # pragma: no cover

    def to_sql_create(self) -> list[str]:
        raise NotImplementedError()

    def to_sql_update(self) -> list[str]:
        return [
            *self.to_sql_drop(),
            *self.to_sql_create(),
        ]

    def to_sql_drop(self) -> list[str]:
        return [f"DROP PROCEDURE {quote_name(self.qualified_name)}();"]

    def with_name(self, name: str):
        return replace(self, name=name)

    def with_language(self, language: str):
        return replace(self, language=language)


@dataclass
class Procedures:
    """The collection of procedures and associated options comparisons.

    Note: `ignore` option accepts a sequence of strings. Each string is individually
        interpreted as a "glob". This means a string like "foo.*" would ignore all views
        contained within the schema "foo".
    """

    procedures: list[Procedure] = field(default_factory=list)

    ignore: list[str] = field(default_factory=list)
    ignore_unspecified: bool = False

    @classmethod
    def coerce_from_unknown(
        cls, unknown: None | Iterable[Procedure] | Procedures
    ) -> Procedures | None:
        if isinstance(unknown, Procedures):
            return unknown

        if isinstance(unknown, Iterable):
            return cls().are(*unknown)

        return None

    @classmethod
    def extract(cls, metadata: MetaData | list[MetaData | None] | None) -> Self | None:
        if not isinstance(metadata, Sequence):
            metadata = [metadata]

        instances: list[Self] = [
            m.info["procedures"] for m in metadata if m and m.info.get("procedures")
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
                "All combined `Procedures` instances must agree on the set of settings: ignore_unspecified"
            )

        procedures = [s for instance in instances for s in instance.procedures]
        ignore = [s for instance in instances for s in instance.ignore]
        ignore_unspecified = instances[0].ignore_unspecified
        return cls(
            procedures=procedures, ignore_unspecified=ignore_unspecified, ignore=ignore
        )

    def append(self, procedure: Procedure):
        self.procedures.append(procedure)

    def __iter__(self):
        yield from self.procedures

    def are(self, *procedures: Procedure):
        return replace(self, procedures=list(procedures))


def register_procedure(base_or_metadata: HasMetaData | MetaData, procedure: Procedure):
    """Register a procedure onto the given declarative base or `Metadata`.

    This can be used instead of the static registration through `Procedures` on a declarative base or
    `MetaData`, to imperitively register procedures.
    """
    if isinstance(base_or_metadata, MetaData):
        metadata = base_or_metadata
    else:
        metadata = base_or_metadata.metadata

    if not metadata.info.get("procedures"):
        metadata.info["procedures"] = Procedures()
    metadata.info["procedures"].append(procedure)
