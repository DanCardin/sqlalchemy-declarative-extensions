from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions.dialects.snowflake import Role, View


def get_schemas_snowflake(connection: Connection):
    from sqlalchemy_declarative_extensions.schema.base import Schema

    schemas_query = text(
        "SELECT schema_name"
        " FROM information_schema.schemata"
        " WHERE lower(schema_name) NOT IN ('information_schema', 'pg_catalog', 'main')"
        " AND catalog_name = current_database()"
    )

    return {
        schema: Schema(schema)
        for schema, *_ in connection.execute(schemas_query).fetchall()
    }


def check_schema_exists_snowflake(connection: Connection, name: str) -> bool:
    schema_exists_query = text(
        "SELECT schema_name"
        " FROM information_schema.schemata"
        " WHERE lower(schema_name) = lower(:schema)"
        " AND catalog_name = current_database()"
    )
    row = connection.execute(schema_exists_query, {"schema": name}).scalar()
    return bool(row)


def get_roles_snowflake(connection: Connection, exclude=None):
    roles_query = text("SHOW ROLES")
    raw_roles = connection.execute(roles_query).fetchall()

    role_members_query = text(
        "SELECT name, grantee_name"
        " FROM snowflake.account_usage.grants_to_roles"
        " WHERE granted_on = 'ROLE'"
        " AND deleted_on IS NULL"
        " AND privilege = 'USAGE'"
    )
    role_members = connection.execute(role_members_query).fetchall()
    role_members_by_grantee: dict[str, list[str]] = {}
    for role, grantee in role_members:
        role_members_by_grantee.setdefault(grantee, []).append(role)

    roles = [
        Role.from_snowflake_role(r, role_members_by_grantee.get(r.name))
        for r in raw_roles
        if exclude and r not in exclude
    ]

    return [*roles]


def get_databases_snowflake(connection: Connection):
    from sqlalchemy_declarative_extensions.database.base import Database

    databases_query = text("SELECT database_name FROM information_schema.databases")

    return {
        database: Database(database)
        for database, *_ in connection.execute(databases_query).fetchall()
    }


def get_dynamic_tables_snowflake(connection: Connection):
    from sqlalchemy_declarative_extensions.dialects.snowflake.dynamic_table import (
        DynamicTable,
    )

    query = text(
        """
            SELECT table_schema, table_name, target_lag, warehouse, text
            FROM information_schema.dynamic_tables
            WHERE table_schema != 'INFORMATION_SCHEMA'
            AND table_catalog = current_database()
        """
    )

    tables = []
    for row in connection.execute(query).fetchall():
        text_str: str = row.text
        text_lower = text_str.lower()
        warehouse_pos = text_lower.find("warehouse")
        as_pos = text_lower.find(" as ", warehouse_pos)
        definition = text_str[as_pos + 4:].strip() if as_pos != -1 else text_str

        schema = row.table_schema if row.table_schema != "PUBLIC" else None
        tables.append(
            DynamicTable(
                name=row.table_name,
                definition=definition,
                target_lag=row.target_lag,
                warehouse=row.warehouse,
                schema=schema,
            )
        )
    return tables


def get_views_snowflake(connection: Connection):
    views_query = text(
        """
            SELECT table_schema AS schema, table_name AS name, view_definition AS definition
            FROM information_schema.views
            WHERE table_schema != 'INFORMATION_SCHEMA'
            AND table_catalog = current_database()
        """
    )

    views = []
    for v in connection.execute(views_query).fetchall():
        schema = v.schema if v.schema != "public" else None

        assert v.definition.startswith("CREATE VIEW")
        *_, definition = v.definition.split(" ", 4)

        view = View(
            v.name,
            definition,
            schema=schema,
        )
        views.append(view)
    return views
