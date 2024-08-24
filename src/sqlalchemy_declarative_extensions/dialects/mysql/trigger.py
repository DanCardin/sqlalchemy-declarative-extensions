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
class Trigger(base.Trigger):
    """Describes a MySQL trigger.

    Some trigger options are not **currently** supported.
    """

    time: TriggerTimes
    event: TriggerEvents
    order: TriggerOrders | None = None
    other_trigger_name: str | None = None

    @classmethod
    def before(
        cls,
        event: TriggerEvents | str,
        on: str,
        execute: str,
        order: TriggerOrders | str | None = None,
        other_trigger_name: str | None = None,
        name: str = "",
    ):
        return cls(
            name=name,
            time=TriggerTimes.before,
            event=TriggerEvents.from_string(event),
            on=on,
            order=order,
            other_trigger_name=other_trigger_name,
            execute=execute,
        )

    @classmethod
    def after(
        cls,
        event: TriggerEvents | str,
        on: str,
        execute: str,
        order: TriggerOrders | str | None = None,
        other_trigger_name: str | None = None,
        name: str = "",
    ):
        return cls(
            name=name,
            time=TriggerTimes.after,
            event=TriggerEvents.from_string(event),
            on=on,
            order=order,
            other_trigger_name=other_trigger_name,
            execute=execute,
        )

    def to_sql_create(self, replace=False) -> str:
        """Return a trigger CREATE statement.

        CREATE
        TRIGGER trigger_name
        { BEFORE | AFTER } { INSERT | UPDATE | DELETE }
        ON table_name FOR EACH ROW
        [{ FOLLOWS | PRECEDES } other_trigger_name]
        trigger_body
        """

        if replace:
            self.to_sql_drop()

        components = ["CREATE"]
        components.append("TRIGGER")
        components.append(self.name)
        components.append(self.time.value)
        components.append(self.event.value)
        components.append("ON")
        components.append(self.on)
        components.append("FOR EACH ROW")
        if self.order:
            components.append(self.order.value)
            components.append(self.other_trigger_name)
        components.append(self.execute)

        return " ".join(components) + ";"

    def to_sql_drop(self) -> str:
        return f"DROP TRIGGER {self.name};"