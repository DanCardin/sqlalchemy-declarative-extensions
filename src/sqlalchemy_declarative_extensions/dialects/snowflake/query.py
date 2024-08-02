from __future__ import annotations
from sqlalchemy_declarative_extensions.sql import qualify_name

from typing import Container

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

    databases_query = text("SELECT database_name" " FROM information_schema.databases")

    return {
        database: Database(database)
        for database, *_ in connection.execute(databases_query).fetchall()
    }


def get_objects_snowflake(connection: Connection):
    return sorted(
        [
            (r.schema, qualify_name(r.schema, r.object_name), r.relkind)
            for r in connection.execute(objects_query).fetchall()
        ]
    )


def get_default_grants_snowflake(
    connection: Connection,
    roles: Container[str] | None = None,
    expanded: bool = False,
):
    default_permissions = connection.execute(
        text("SHOW FUTURE GRANTS IN DATABASE CURRENT_DATABASE;")
    ).fetchall()

    assert connection.engine.url.username
    current_role: str = connection.engine.url.username

    result = []
    for permission in default_permissions:
        for acl_item in permission.acl:
            default_grants = parse_default_acl(
                acl_item,
                permission.object_type,
                permission.schema_name,
                current_role=current_role,
                expanded=expanded,
            )
            for default_grant in default_grants:
                if roles is None or default_grant.grant.target_role in roles:
                    result.append(default_grant)

    return result


def get_grants_snowflake(
    connection: Connection,
    roles: Container[str] | None = None,
    expanded=False,
):
    existing_permissions = connection.execute(
        text(
            """
            SELECT * FROM skeptic.information_schema.object_privileges
            WHERE
              (
                OBJECT_CATALOG = 'SKEPTIC'
                OR OBJECT_TYPE = 'DATABASE' AND OBJECT_NAME = 'SKEPTIC'
              );
            """
        )
    ).fetchall()

    result = []
    for permission in existing_permissions:
        acl = permission.acl
        if acl is None:
            acl = [acl]

        for acl_item in acl:
            grants = parse_acl(
                acl_item,
                permission.relkind,
                qualify_name(permission.schema, permission.name),
                owner=permission.owner,
                expanded=expanded,
            )
            for grant in grants:
                if roles is None or grant.grant.target_role in roles:
                    result.append(grant)

    return result
