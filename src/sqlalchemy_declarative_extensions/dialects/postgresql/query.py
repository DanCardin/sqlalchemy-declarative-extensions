from __future__ import annotations

from typing import Container, Optional

from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions.dialects.postgresql.acl import (
    parse_acl,
    parse_default_acl,
)
from sqlalchemy_declarative_extensions.dialects.postgresql.schema import (
    default_acl_query,
    object_acl_query,
    objects_query,
    roles_query,
)


def get_objects_postgresql(connection: Connection):
    return sorted(connection.execute(objects_query).fetchall())


def get_roles_postgresql(connection: Connection, exclude=None):
    from sqlalchemy_declarative_extensions.role import PGRole

    result = [
        PGRole.from_pg_role(r)
        for r in connection.execute(roles_query).fetchall()
        if not r.rolname.startswith("pg_")
    ]
    if exclude:
        result = [role for role in result if role.name not in exclude]
    return result


def get_default_grants_postgresql(
    connection: Connection,
    roles: Optional[Container[str]] = None,
):
    default_permissions = connection.execute(default_acl_query).fetchall()

    result = []
    for permission in default_permissions:
        for acl_item in permission.acl:
            default_grants = parse_default_acl(
                acl_item,
                permission.object_type,
                permission.schema_name,
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


def qualify_name(schema, name):
    if schema == "public":
        return name
    return f"{schema}.{name}"
