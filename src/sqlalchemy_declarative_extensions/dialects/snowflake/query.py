from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions.dialects.snowflake import Role


def get_schemas_snowflake(connection: Connection):
    from sqlalchemy_declarative_extensions.schema.base import Schema

    schemas_query = text(
        "SELECT schema_name"
        " FROM information_schema.schemata"
        " WHERE lower(schema_name) NOT IN ('information_schema', 'pg_catalog', 'main')"
    )

    return {
        Schema(schema) for schema, *_ in connection.execute(schemas_query).fetchall()
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
