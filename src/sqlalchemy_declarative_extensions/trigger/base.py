from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Hashable, Iterable, Sequence

from sqlalchemy import MetaData, Table
from sqlalchemy.engine import Connection
from sqlalchemy.sql.schema import SchemaItem
from typing_extensions import Self

from sqlalchemy_declarative_extensions.sql import qualify_name
from sqlalchemy_declarative_extensions.sqlalchemy import HasMetaData


@dataclass
class Trigger(SchemaItem):
    """Describes a generic trigger."""

    name: str
    on: str
    execute: str

    @property
    def identity(self) -> Hashable:
        """Return the dialect-specific identity used to compare triggers."""
        return self.name

    def named(self, name: str):
        return replace(self, name=name)

    def _set_parent(self, parent: Any, **kw: Any) -> None:
        """Attach to the `Table` __table_args__ it was declared in."""
        if not isinstance(parent, Table):
            raise ValueError(
                f"Trigger can only be attached to a `Table`, got: {parent}."
            )

        on = qualify_name(parent.schema, parent.name)
        if not self.name:
            raise ValueError(f"Trigger attached to table '{on}' must have a name.")

        if self.on and self.on != on:
            raise ValueError(
                f"Trigger '{self.name}' declares `on='{self.on}'`,"
                f" which conflicts with the table it is attached to: '{on}'."
            )

        register_trigger(parent.metadata, replace(self, on=on))

    def to_sql_create(self):
        raise NotImplementedError()

    def to_sql_update(self, connection: Connection | None = None):
        return [
            self.to_sql_drop(),
            self.to_sql_create(),
        ]

    def to_sql_drop(self):
        return f"DROP TRIGGER {self.name} ON {self.on};"


@dataclass
class Triggers:
    triggers: list[Trigger] = field(default_factory=list)

    include: list[str] | None = None
    ignore: list[str] = field(default_factory=list)
    ignore_unspecified: bool = False

    @classmethod
    def coerce_from_unknown(
        cls, unknown: None | Iterable[Trigger] | Triggers
    ) -> Triggers | None:
        if isinstance(unknown, Triggers):
            return unknown

        if isinstance(unknown, Iterable):
            return cls().are(*unknown)

        return None

    @classmethod
    def extract(cls, metadata: MetaData | list[MetaData | None] | None) -> Self | None:
        if not isinstance(metadata, Sequence):
            metadata = [metadata]

        instances: list[Self] = [
            m.info["triggers"] for m in metadata if m and m.info.get("triggers")
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
                "All combined `Triggers` instances must agree on the set of settings: ignore_unspecified"
            )

        triggers = [s for instance in instances for s in instance.triggers]
        # Preserve None if all instances have include=None, otherwise combine all non-None includes
        include_values = [
            instance.include for instance in instances if instance.include is not None
        ]
        include = [s for inc in include_values for s in inc] if include_values else None
        ignore = [s for instance in instances for s in instance.ignore]
        ignore_unspecified = instances[0].ignore_unspecified
        return cls(
            triggers=triggers,
            ignore_unspecified=ignore_unspecified,
            ignore=ignore,
            include=include,
        )

    def append(self, trigger: Trigger):
        self.triggers.append(trigger)

    def __iter__(self):
        yield from self.triggers

    def are(self, *triggers: Trigger):
        return replace(self, triggers=list(triggers))


def register_trigger(base_or_metadata: HasMetaData | MetaData, trigger: Trigger):
    """Register a trigger onto the given declarative base or `Metadata`.

    This can be used instead of the static registration through `Triggers` on a declarative base or
    `MetaData`, to imperitively register triggers.
    """
    if isinstance(base_or_metadata, MetaData):
        metadata = base_or_metadata
    else:
        metadata = base_or_metadata.metadata

    if not metadata.info.get("triggers"):
        metadata.info["triggers"] = Triggers()
    metadata.info["triggers"].append(trigger)
