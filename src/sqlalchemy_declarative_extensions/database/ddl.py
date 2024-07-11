from __future__ import annotations

from sqlalchemy import MetaData, text
from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions.database import Databases
from sqlalchemy_declarative_extensions.database.compare import compare_databases
from sqlalchemy_declarative_extensions.role.compare import UseRoleOp
from sqlalchemy_declarative_extensions.sql import match_name


def database_ddl(databases: Databases, database_filter: list[str] | None = None):
    def receive_after_create(metadata: MetaData, connection: Connection, **_):
        result = compare_databases(connection, databases)
        for op in result:
            if not isinstance(op, UseRoleOp) and not match_name(
                op.database.name, database_filter
            ):
                continue

            for statement in op.to_sql():
                connection.execute(text(statement))

    return receive_after_create
