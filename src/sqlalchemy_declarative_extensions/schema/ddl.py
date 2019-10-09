from sqlalchemy.engine.base import Connection
from sqlalchemy.schema import CreateSchema
from sqlalchemy.sql import text

from sqlalchemy_declarative_extensions.schema import Schema
from sqlalchemy_declarative_extensions.sqlalchemy import dialect_dispatch


def schema_ddl(schema: Schema):
    ddl = CreateSchema(schema.name)
    return ddl.execute_if(callable_=check_schema)  # type: ignore


def check_schema(ddl, target, connection, **_):
    schema = ddl.element
    return schema_exists(connection, name=schema)


def schema_exists_sqlite(connection: Connection, name: str) -> bool:
    """Check whether the given schema exists.

    For `sqlalchemy.schema.CreateSchema` to work, we need to first attach
    a :memory: as the given schema name first. Given that they need to be
    created anew for each new connection, we can (hopefully) safely,
    unconditionally attach it and return `False` always.
    """
    schema_exists = "ATTACH DATABASE ':memory:' AS :schema"
    connection.execute(schema_exists, schema=name)
    return False


def schema_exists_postgresql(connection: Connection, name: str) -> bool:
    """Check whether the given schema exists."""
    schema_exists = text(
        "SELECT schema_name FROM information_schema.schemata WHERE schema_name = :schema"
    )
    row = connection.execute(schema_exists, schema=name).scalar()
    return not bool(row)


schema_exists = dialect_dispatch(
    postgresql=schema_exists_postgresql,
    sqlite=schema_exists_sqlite,
)
