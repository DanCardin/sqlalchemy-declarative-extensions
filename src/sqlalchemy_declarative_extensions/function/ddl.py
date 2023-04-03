from sqlalchemy import MetaData, text
from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions import Functions
from sqlalchemy_declarative_extensions.function.compare import compare_functions


def function_ddl(functions: Functions):
    def after_create(metadata: MetaData, connection: Connection, **_):
        result = compare_functions(connection, functions, metadata)
        for op in result:
            command = op.to_sql()
            connection.execute(text(command))

    return after_create
