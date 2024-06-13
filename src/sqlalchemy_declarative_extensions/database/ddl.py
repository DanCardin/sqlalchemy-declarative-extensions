from __future__ import annotations

from sqlalchemy import MetaData, text
from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions.database import Databases
from sqlalchemy_declarative_extensions.database.compare import compare_databases


def database_ddl(metadata: MetaData, connection: Connection, **_):
    databases: Databases | None = metadata.info.get("databases")
    if not databases:  # pragma: no cover
        return

    result = compare_databases(connection, databases)
    for op in result:
        for statement in op.to_sql():
            connection.execute(text(statement))
