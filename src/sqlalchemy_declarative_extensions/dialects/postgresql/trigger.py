from __future__ import annotations

from dataclasses import dataclass, replace

from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions.dialects.from_string import FromStrings
from sqlalchemy_declarative_extensions.sql import quote_name
from sqlalchemy_declarative_extensions.trigger import base


class TriggerTimes(FromStrings):
    before = "BEFORE"
    after = "AFTER"
    instead_of = "INSTEAD OF"

    @classmethod
    def from_bit_string(cls, bitstring: str):
        """Parse a postgres "tgtype" bit string into a concrete variant.

        Per https://github.com/postgres/postgres/blob/master/src/include/catalog/pg_trigger.h
        """
        instead = int(bitstring) & (1 << 6)
        if instead:
            return cls.instead_of

        before = int(bitstring) & (1 << 1)
        if before:
            return cls.before

        return cls.after


class TriggerForEach(FromStrings):
    row = "ROW"
    statement = "STATEMENT"

    @classmethod
    def from_bit_string(cls, bitstring: str):
        """Parse a postgres "tgtype" bit string into a concrete variant.

        Per https://github.com/postgres/postgres/blob/master/src/include/catalog/pg_trigger.h
        """
        result = int(bitstring) & (1 << 0)
        if result == 0:
            return cls.statement

        return cls.row


class TriggerEvents(FromStrings):
    insert = "INSERT"
    update = "UPDATE"
    delete = "DELETE"
    truncate = "TRUNCATE"

    @classmethod
    def from_bit_string(cls, bitstring: str) -> list[TriggerEvents]:
        """Parse a postgres "tgtype" bit string into a concrete variant.

        Per https://github.com/postgres/postgres/blob/master/src/include/catalog/pg_trigger.h
        """
        insert = int(bitstring) & (1 << 2)
        delete = int(bitstring) & (1 << 3)
        update = int(bitstring) & (1 << 4)
        truncate = int(bitstring) & (1 << 5)

        assert not (truncate and (insert or delete or update))

        result = []
        if insert:
            result.append(cls.insert)
        if update:
            result.append(cls.update)
        if delete:
            result.append(cls.delete)
        if truncate:
            result.append(cls.truncate)
        return result


@dataclass
class Trigger(base.Trigger):
    """Describes a PostgreSQL trigger.

    Some trigger options are not **currently** supported.
    """

    events: list[TriggerEvents]
    time: TriggerTimes
    for_each: TriggerForEach = TriggerForEach.statement
    condition: str | None = None
    arguments: tuple[str, ...] | None = None

    @classmethod
    def before(
        cls, *events: TriggerEvents | str, on: str, execute: str, name: str = ""
    ):
        return cls(
            time=TriggerTimes.before,
            events=TriggerEvents.from_strings(events),
            on=on,
            execute=execute,
            name=name,
        )

    @classmethod
    def after(cls, *events: TriggerEvents | str, on: str, execute: str, name: str = ""):
        return cls(
            time=TriggerTimes.after,
            events=TriggerEvents.from_strings(events),
            on=on,
            execute=execute,
            name=name,
        )

    @classmethod
    def instead_of(
        cls, *events: TriggerEvents | str, on: str, execute: str, name: str = ""
    ):
        return cls(
            time=TriggerTimes.instead_of,
            events=TriggerEvents.from_strings(events),
            on=on,
            execute=execute,
            name=name,
        )

    def for_each_row(self):
        return replace(self, for_each=TriggerForEach.row)

    def for_each_statement(self):
        return replace(self, for_each=TriggerForEach.statement)

    def when(self, condition: str):
        return replace(self, condition=condition)

    def with_arguments(self, *arguments: str):
        return replace(self, arguments=arguments)

    def to_sql_create(self, replace=False):
        """Return a trigger CREATE statement.

        CREATE [ OR REPLACE ] [ CONSTRAINT ] TRIGGER name { BEFORE | AFTER | INSTEAD OF } { event [ OR ... ] }
        ON table_name
        [ FROM referenced_table_name ]
        [ NOT DEFERRABLE | [ DEFERRABLE ] [ INITIALLY IMMEDIATE | INITIALLY DEFERRED ] ]
        [ REFERENCING { { OLD | NEW } TABLE [ AS ] transition_relation_name } [ ... ] ]
        [ FOR [ EACH ] { ROW | STATEMENT } ]
        [ WHEN ( condition ) ]
        EXECUTE { FUNCTION | PROCEDURE } function_name ( arguments )
        """
        components = ["CREATE"]

        if replace:
            components.append("OR REPLACE")

        components.append("TRIGGER")
        components.append(quote_name(self.name))
        components.append(self.time.value)
        components.append(" OR ".join([e.value for e in self.events]))
        components.append("ON")

        components.append(quote_name(self.on))

        components.append("FOR EACH")
        components.append(self.for_each.value)

        if self.condition:
            components.append("WHEN")
            components.append(f"({self.condition})")

        components.append("EXECUTE PROCEDURE")
        args_quoted = (
            tuple(f"'{arg}'" for arg in self.arguments) if self.arguments else ()
        )
        components.append(quote_name(self.execute) + f"({','.join(args_quoted)})")
        return " ".join(components) + ";"

    def to_sql_update(self, connection: Connection | None = None):
        if connection is not None:
            assert connection.dialect.server_version_info
            if connection.dialect.server_version_info >= (14, 0):
                return [self.to_sql_create(replace=True)]

        return super().to_sql_update(connection)
