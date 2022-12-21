from sqlalchemy import text
from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions.dialects.sqlite.schema import (
    table_exists_query,
    views_query,
)
from sqlalchemy_declarative_extensions.view.base import View


def check_schema_exists_sqlite(connection: Connection, name: str) -> bool:
    """Check whether the given schema exists.

    For `sqlalchemy.schema.CreateSchema` to work, we need to first attach
    a :memory: as the given schema name first. Given that they need to be
    created anew for each new connection, we can (hopefully) safely,
    unconditionally attach it and return `False` always.
    """
    schema_exists = "ATTACH DATABASE ':memory:' AS :schema"
    connection.execute(text(schema_exists), {"schema": name})
    return False


def get_views_sqlite(connection: Connection):
    return [
        View(v.name, v.definition, schema=v.schema)
        for v in connection.execute(views_query()).fetchall()
    ]


def check_table_exists_sqlite(
    connection: Connection, name: str, *, schema: str
) -> bool:
    row = connection.execute(
        table_exists_query(schema),
        {"name": name, "schema": schema},
    ).scalar()
    return bool(row)
