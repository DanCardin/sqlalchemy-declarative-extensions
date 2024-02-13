from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.engine.base import Connection
from sqlalchemy.sql.expression import text

from sqlalchemy_declarative_extensions.dialects.snowflake import Role


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


def get_roles_snowflake(connection: Connection, exclude=None):
    roles_query = text("SHOW USERS")

    raw_roles = connection.execute(roles_query).fetchall()

    result = [Role.from_snowflake_role(r) for r in raw_roles]
    if exclude:
        return [role for role in result if role.name not in exclude]
    return result
