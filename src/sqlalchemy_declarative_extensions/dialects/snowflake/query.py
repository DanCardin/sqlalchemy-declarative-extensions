from __future__ import annotations

from sqlalchemy.engine.base import Connection
from sqlalchemy.sql.expression import text

from sqlalchemy_declarative_extensions.view.base import View


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


def get_views_snowflake(connection: Connection):
    database = connection.engine.url.database
    query = text(
        """
        SELECT
            TABLE_SCHEMA AS schema,
            TABLE_NAME AS name,
            VIEW_DEFINITION AS definition
        FROM information_schema.views
        WHERE TABLE_CATALOG = :database
        WHERE TABLE_NAME != 'information_schema'
        """
    )
    db_views = connection.execute(query, {"database": database}).fetchall()

    views = []
    for v in db_views:
        schema = v.schema_name if v.schema_name != "public" else None

        view = View(v.name, normalize_view_definintion(v.definition), schema=schema)
        views.append(view)
    return views


def get_view_snowflake(connection: Connection, name: str, schema: str = "public"):
    database = connection.engine.url.database
    query = text(
        """
        SELECT
            TABLE_SCHEMA AS schema,
            TABLE_NAME AS name,
            VIEW_DEFINITION AS definition
        FROM information_schema.views
        WHERE TABLE_CATALOG = :database
        WHERE TABLE_SCHEMA = :schema
        WHERE TABLE_NAME = :name
        """
    )
    result = connection.execute(
        query, {"database": database, "schema": schema, "name": name}
    ).fetchone()
    assert result

    view_schema = result.schema_name if result.schema != "public" else None
    return View(
        result.name, normalize_view_definintion(result.definition), schema=view_schema
    )


def normalize_view_definintion(sql: str) -> str:
    index = sql.find("AS ")
    result = sql[index + 3 :].strip()
    print(result)
    return result
