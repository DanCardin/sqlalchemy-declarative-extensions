from sqlalchemy import text
from sqlalchemy.engine import Connection


def check_schema_exists_sqlite(connection: Connection, name: str) -> bool:
    """Check whether the given schema exists.

    For `sqlalchemy.schema.CreateSchema` to work, we need to first attach
    a :memory: as the given schema name first. Given that they need to be
    created anew for each new connection, we can (hopefully) safely,
    unconditionally attach it and return `False` always.
    """
    schema_exists = "ATTACH DATABASE ':memory:' AS :schema"
    connection.execute(text(schema_exists), schema=name)
    return False
