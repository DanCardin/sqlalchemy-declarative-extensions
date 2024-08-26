from __future__ import annotations

from dataclasses import dataclass, replace

from sqlalchemy_declarative_extensions.dialects.from_string import FromStrings
from sqlalchemy_declarative_extensions.trigger import base


class TriggerTimes(FromStrings):
    before = "BEFORE"
    after = "AFTER"


class TriggerEvents(FromStrings):
    insert = "INSERT"
    update = "UPDATE"
    delete = "DELETE"


class TriggerOrders(FromStrings):
    follows = "FOLLOWS"
    precedes = "PRECEDES"


@dataclass
class TriggerOrder:
    """Encodes the trigger order.

    MySQL triggers can be (optionally) made to execute before/after a related trigger.
    """

    order: TriggerOrders
    other_trigger_name: str


@dataclass
class Trigger(base.Trigger):
    """Describes a MySQL trigger.

    Some trigger options are not **currently** supported.
    """

    time: TriggerTimes
    event: TriggerEvents
    order: TriggerOrder | None = None

    @classmethod
    def before(
        cls,
        event: TriggerEvents | str,
        on: str,
        execute: str,
        name: str = "",
    ):
        return cls(
            name=name,
            time=TriggerTimes.before,
            event=TriggerEvents.from_string(event),
            on=on,
            execute=execute,
        )

    @classmethod
    def after(
        cls,
        event: TriggerEvents | str,
        on: str,
        execute: str,
        name: str = "",
    ):
        return cls(
            name=name,
            time=TriggerTimes.after,
            event=TriggerEvents.from_string(event),
            on=on,
            execute=execute,
        )

    def follows(self, other_trigger_name: str):
        """Set the trigger to be ordered **after** the provided trigger name."""
        return replace(
            self, order=TriggerOrder(TriggerOrders.follows, other_trigger_name)
        )

    def precedes(self, other_trigger_name: str):
        """Set the trigger to be ordered **before** the provided trigger name."""
        return replace(
            self, order=TriggerOrder(TriggerOrders.precedes, other_trigger_name)
        )

    def to_sql_create(self) -> str:
        """Return a trigger CREATE statement.

        CREATE
        TRIGGER trigger_name
        { BEFORE | AFTER } { INSERT | UPDATE | DELETE }
        ON table_name FOR EACH ROW
        [{ FOLLOWS | PRECEDES } other_trigger_name]
        trigger_body
        """
        components = ["CREATE"]
        components.append("TRIGGER")
        components.append(self.name)
        components.append(self.time.value)
        components.append(self.event.value)
        components.append("ON")
        components.append(self.on)
        components.append("FOR EACH ROW")
        if self.order:
            components.append(self.order.order.value)
            components.append(self.order.other_trigger_name)
        components.append(self.execute)

        return " ".join(components) + ";"

    def to_sql_drop(self) -> str:
        return f"DROP TRIGGER {self.name};"
