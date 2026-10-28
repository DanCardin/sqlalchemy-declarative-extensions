from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions.dialects import get_triggers
from sqlalchemy_declarative_extensions.op import ExecuteOp
from sqlalchemy_declarative_extensions.sql import filter_ignored
from sqlalchemy_declarative_extensions.trigger.base import Trigger, Triggers


@dataclass
class CreateTriggerOp(ExecuteOp):
    trigger: Trigger

    def reverse(self):
        return DropTriggerOp(self.trigger)

    def to_sql(self, connection: Connection | None = None) -> list[str]:
        return [self.trigger.to_sql_create()]


@dataclass
class UpdateTriggerOp(ExecuteOp):
    from_trigger: Trigger
    trigger: Trigger

    def reverse(self):
        return UpdateTriggerOp(from_trigger=self.trigger, trigger=self.from_trigger)

    def to_sql(self, connection: Connection | None = None) -> list[str]:
        return self.trigger.to_sql_update(connection)


@dataclass
class DropTriggerOp(ExecuteOp):
    trigger: Trigger

    def reverse(self):
        return CreateTriggerOp(self.trigger)

    def to_sql(self, connection: Connection | None = None) -> list[str]:
        return [self.trigger.to_sql_drop()]


Operation = Union[CreateTriggerOp, UpdateTriggerOp, DropTriggerOp]


def compare_triggers(connection: Connection, triggers: Triggers) -> list[Operation]:
    result: list[Operation] = []

    triggers_by_identity = {r.identity: r for r in triggers.triggers}
    expected_trigger_identities = set(triggers_by_identity)

    raw_existing_triggers = get_triggers(connection)
    existing_triggers = filter_ignored(
        raw_existing_triggers,
        triggers.ignore,
        include=triggers.include,
        key=lambda t: t.name,
    )

    existing_triggers_by_identity = {r.identity: r for r in existing_triggers}
    existing_trigger_identities = set(existing_triggers_by_identity)

    new_trigger_identities = expected_trigger_identities - existing_trigger_identities
    removed_trigger_identities = (
        existing_trigger_identities - expected_trigger_identities
    )

    for trigger in triggers:
        trigger_created = trigger.identity in new_trigger_identities

        if trigger_created:
            result.append(CreateTriggerOp(trigger))
        else:
            existing_trigger = existing_triggers_by_identity[trigger.identity]

            if existing_trigger != trigger:
                result.append(UpdateTriggerOp(existing_trigger, trigger))

    if not triggers.ignore_unspecified:
        for removed_trigger in removed_trigger_identities:
            trigger = existing_triggers_by_identity[removed_trigger]
            result.append(DropTriggerOp(trigger))

    return result
