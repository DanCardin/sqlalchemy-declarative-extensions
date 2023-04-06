from sqlalchemy import MetaData, text
from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions import Triggers
from sqlalchemy_declarative_extensions.trigger.compare import compare_triggers


def trigger_ddl(triggers: Triggers):
    def after_create(metadata: MetaData, connection: Connection, **_):
        result = compare_triggers(connection, triggers, metadata)
        for op in result:
            for command in op.to_sql(connection):
                connection.execute(text(command))

    return after_create
