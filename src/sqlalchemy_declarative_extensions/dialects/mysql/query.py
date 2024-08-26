from __future__ import annotations

from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions.dialects.mysql.schema import (
    schema_exists_query,
    triggers_query,
    views_query,
)
from sqlalchemy_declarative_extensions.dialects.mysql.trigger import (
    Trigger,
    TriggerEvents,
    TriggerTimes,
)
from sqlalchemy_declarative_extensions.view.base import View


def get_views_mysql(connection: Connection):
    current_database = connection.engine.url.database
    return [
        View(
            v.name,
            v.definition,
            schema=v.schema if v.schema != current_database else None,
        )
        for v in connection.execute(views_query).fetchall()
    ]


def get_triggers_mysql(connection: Connection) -> list[Trigger]:
    triggers = []
    for t in connection.execute(triggers_query).fetchall():
        triggers.append(
            Trigger(
                name=t.name,
                time=TriggerTimes(t.time),
                event=TriggerEvents(t.event),
                on=t.on_name,
                execute=t.statement,
            )
        )
    return triggers


def check_schema_exists_mysql(connection: Connection, name: str) -> bool:
    row = connection.execute(schema_exists_query, {"schema": name}).scalar()
    return not bool(row)
