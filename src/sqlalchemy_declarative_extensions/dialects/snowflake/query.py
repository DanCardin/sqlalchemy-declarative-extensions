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
    )
    row = connection.execute(schema_exists_query, {"schema": name}).scalar()
    return bool(row)


def get_roles_snowflake(connection: Connection, exclude=None):
    roles_query = text("SHOW ROLES")
    raw_roles = connection.execute(roles_query).fetchall()

    role_members_query = text(
        "select name, grantee_name from snowflake.account_usage.grants_to_roles where granted_on = 'ROLE' and deleted_on is null and privilege = 'USAGE';"
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


def get_views_snowflake(connection: Connection):
    compound_database = connection.engine.url.database
    assert compound_database
    database, *_ = compound_database.split("/", 1)
    database = database.upper()

    views_query = text(
        """
            SELECT table_schema AS schema, table_name AS name, view_definition AS definition
            FROM information_schema.views
            WHERE table_schema != 'INFORMATION_SCHEMA'
            AND table_catalog = :database
        """
    )

    views = []
    for v in connection.execute(views_query, {"database": database}).fetchall():
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
