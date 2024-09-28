from __future__ import annotations

from sqlalchemy import MetaData, text
from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions import Triggers
from sqlalchemy_declarative_extensions.sql import match_name
from sqlalchemy_declarative_extensions.trigger.compare import compare_triggers


def trigger_ddl(triggers: Triggers, trigger_filter: list[str] | None = None):
    def after_create(metadata: MetaData, connection: Connection, **_):
        result = compare_triggers(connection, triggers)
        for op in result:
            if not match_name(op.trigger.name, trigger_filter):
                continue

            for command in op.to_sql(connection):
                connection.execute(text(command))

    return after_create
