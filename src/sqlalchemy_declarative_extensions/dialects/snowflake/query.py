from __future__ import annotations

import warnings
from collections.abc import Iterable

from sqlalchemy import text
from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions.dialects.snowflake import Role, View
from sqlalchemy_declarative_extensions.sql import is_ignored, qualify_name


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


def get_views_snowflake(
    connection: Connection,
    ignore: Iterable[str] = (),
    include: Iterable[str] | None = None,
):
    """Fetch the views of the current database.

    Views matching any of the `ignore` globs, or (when `include` is given) none of the
    `include` globs, are never introspected, so (for example) views which the current
    role cannot see the definition of, but which are excluded anyway, do not interfere.
    """
    ignore = list(ignore)
    include = None if include is None else list(include)

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

        # Snowflake identifiers are case-insensitive unless quoted, and it reports them uppercase.
        qualified_name = qualify_name(schema, v.name)
        if is_ignored(qualified_name, ignore, include=include, case_sensitive=False):
            continue

        # `view_definition` is NULL for views the current role does not have access to. Since we
        # cant do anything with them, we'll loudly skip them to avoid a confusing autogenerate result
        # where it tries to edit those views.
        if v.definition is None:
            warnings.warn(
                f"Skipping view '{qualified_name}': its definition is not visible to the"
                " current role. Ignore it explicitly (`Views(ignore=[...])`), or leave it out of"
                " `Views(include=[...])`, to silence this.",
                stacklevel=2,
            )
            continue

        assert v.definition.startswith("CREATE VIEW")
        *_, definition = v.definition.split(" ", 4)

        view = View(
            v.name,
            definition,
            schema=schema,
        )
        views.append(view)
    return views
