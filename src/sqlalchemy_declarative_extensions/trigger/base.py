from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Iterable

from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions.sqlalchemy import HasMetaData, MetaData


@dataclass
class Trigger:
    """Describes a generic trigger."""

    name: str
    on: str
    execute: str

    def named(self, name: str):
        return replace(self, name=name)

    def to_sql_create(self, replace=False):
        raise NotImplementedError()

    def to_sql_update(self, connection: Connection):
        assert connection.dialect.server_version_info
        if connection.dialect.server_version_info >= (14, 0):
            return [self.to_sql_create(replace=True)]

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

    def append(self, trigger: Trigger):
        self.triggers.append(trigger)

    def __iter__(self):
        yield from self.triggers

    def are(self, *triggers: Trigger):
        return replace(self, triggers=triggers)


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
