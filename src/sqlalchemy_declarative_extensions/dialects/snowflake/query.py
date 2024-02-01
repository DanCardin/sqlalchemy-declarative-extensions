from __future__ import annotations

from sqlalchemy.engine.base import Connection
from sqlalchemy.sql.expression import text


def get_schemas_snowflake(connection: Connection):
    from sqlalchemy_declarative_extensions.schema.base import Schema

    schemas_query = text(
        "SELECT schema_name"
        " FROM information_schema.schemata"
        " WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'main')"
    )

    return {
        Schema(schema) for schema, *_ in connection.execute(schemas_query).fetchall()
    }


def check_schema_exists_snowflake(connection: Connection, name: str) -> bool:
    schema_exists_query = text(
        "SELECT schema_name"
        " FROM information_schema.schemata"
        " WHERE schema_name = :schema"
    )
    row = connection.execute(schema_exists_query, {"schema": name}).scalar()
    return bool(row)
