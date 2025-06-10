from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Iterable, Sequence

from sqlalchemy import MetaData
from sqlalchemy.engine import Connection
from typing_extensions import Self

from sqlalchemy_declarative_extensions.sqlalchemy import HasMetaData


@dataclass
class Trigger:
    """Describes a generic trigger."""

    name: str
    on: str
    execute: str

    def named(self, name: str):
        return replace(self, name=name)

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
        ignore_unspecified = instances[0].ignore_unspecified
        return cls(triggers=triggers, ignore_unspecified=ignore_unspecified)

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
