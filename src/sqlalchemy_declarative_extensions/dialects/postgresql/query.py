from __future__ import annotations

from typing import Container, Optional

from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions.dialects.postgresql.acl import (
    parse_acl,
    parse_default_acl,
)
from sqlalchemy_declarative_extensions.dialects.postgresql.role import Role
from sqlalchemy_declarative_extensions.dialects.postgresql.schema import (
    default_acl_query,
    object_acl_query,
    objects_query,
    roles_query,
    schema_exists_query,
    schemas_query,
)


def get_schemas_postgresql(connection: Connection):
    from sqlalchemy_declarative_extensions.schema.base import Schema

    return {
        Schema(schema) for schema, *_ in connection.execute(schemas_query).fetchall()
    }


def check_schema_exists_postgresql(connection: Connection, name: str) -> bool:
    row = connection.execute(schema_exists_query, schema=name).scalar()
    return not bool(row)


def get_objects_postgresql(connection: Connection):
    return sorted(
        [
            (r.schema, qualify_name(r.schema, r.object_name), r.relkind)
            for r in connection.execute(objects_query).fetchall()
        ]
    )


def get_default_grants_postgresql(
    connection: Connection,
    roles: Optional[Container[str]] = None,
    expanded: bool = False,
):
    default_permissions = connection.execute(default_acl_query).fetchall()
    current_role: str = connection.engine.url.username  # type: ignore

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


def get_grants_postgresql(
    connection: Connection,
    roles: Optional[Container[str]] = None,
    expanded=False,
):
    existing_permissions = connection.execute(object_acl_query).fetchall()

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


def get_roles_postgresql(connection: Connection, exclude=None):
    result = [
        Role.from_pg_role(r)
        for r in connection.execute(roles_query).fetchall()
        if not r.rolname.startswith("pg_")
    ]
    if exclude:
        result = [role for role in result if role.name not in exclude]
    return result


def qualify_name(schema, name):
    if schema == "public":
        return name
    return f"{schema}.{name}"
