from __future__ import annotations

from sqlalchemy import MetaData, text
from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions import Functions
from sqlalchemy_declarative_extensions.function.compare import compare_functions
from sqlalchemy_declarative_extensions.sql import match_name


def function_ddl(functions: Functions, function_filter: list[str] | None = None):
    def after_create(metadata: MetaData, connection: Connection, **_):
        result = compare_functions(connection, functions)
        for op in result:
            if not match_name(op.function.qualified_name, function_filter):
                continue

            commands = op.to_sql()
            for command in commands:
                connection.execute(text(command))

    return after_create
