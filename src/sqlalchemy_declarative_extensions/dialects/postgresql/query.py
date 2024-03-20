from __future__ import annotations

from typing import Container, List, cast

from sqlalchemy import Index, UniqueConstraint
from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions.dialects.postgresql.acl import (
    parse_acl,
    parse_default_acl,
)
from sqlalchemy_declarative_extensions.dialects.postgresql.function import Function
from sqlalchemy_declarative_extensions.dialects.postgresql.role import Role
from sqlalchemy_declarative_extensions.dialects.postgresql.schema import (
    default_acl_query,
    functions_query,
    object_acl_query,
    objects_query,
    roles_query,
    schema_exists_query,
    schemas_query,
    triggers_query,
    view_query,
    views_query,
)
from sqlalchemy_declarative_extensions.dialects.postgresql.trigger import (
    Trigger,
    TriggerEvents,
    TriggerForEach,
    TriggerTimes,
)
from sqlalchemy_declarative_extensions.sql import qualify_name
from sqlalchemy_declarative_extensions.view.base import View, ViewIndex


def get_schemas_postgresql(connection: Connection):
    from sqlalchemy_declarative_extensions.schema.base import Schema

    return {
        Schema(schema) for schema, *_ in connection.execute(schemas_query).fetchall()
    }


def check_schema_exists_postgresql(connection: Connection, name: str) -> bool:
    row = connection.execute(schema_exists_query, {"schema": name}).scalar()
    return bool(row)


def get_objects_postgresql(connection: Connection):
    return sorted(
        [
            (r.schema, qualify_name(r.schema, r.object_name), r.relkind)
            for r in connection.execute(objects_query).fetchall()
        ]
    )


def get_default_grants_postgresql(
    connection: Connection,
    roles: Container[str] | None = None,
    expanded: bool = False,
):
    default_permissions = connection.execute(default_acl_query).fetchall()

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


def get_grants_postgresql(
    connection: Connection,
    roles: Container[str] | None = None,
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
    raw_roles = connection.execute(roles_query).fetchall()

    result = [Role.from_pg_role(r) for r in raw_roles]
    if exclude:
        return [role for role in result if role.name not in exclude]
    return result


def get_views_postgresql(connection: Connection):
    views = []
    for v in connection.execute(views_query).fetchall():
        schema = v.schema if v.schema != "public" else None

        indexes: list[ViewIndex | Index | UniqueConstraint] = [
            ViewIndex(
                name=raw["name"],
                unique=raw["unique"],
                columns=cast(List[str], raw["column_names"]),
            )
            for raw in connection.dialect.get_indexes(connection, v.name, schema=schema)
        ]
        view = View(
            v.name,
            v.definition,
            schema=schema,
            materialized=v.materialized,
            constraints=indexes or None,
        )
        views.append(view)
    return views


def get_view_postgresql(connection: Connection, name: str, schema: str = "public"):
    result = connection.execute(view_query, {"schema": schema, "name": name}).fetchone()
    assert result
    return View(
        result.name,
        result.definition,
        schema=result.schema if result.schema != "public" else None,
    )


def get_functions_postgresql(connection: Connection) -> list[Function]:
    functions = []
    for f in connection.execute(functions_query).fetchall():
        function = Function(
            name=f.name,
            definition=f.source,
            returns=f.return_type,
            language=f.language,
            schema=f.schema if f.schema != "public" else None,
        )
        functions.append(function)
    return functions


def get_triggers_postgresql(connection: Connection):
    triggers = []
    for t in connection.execute(triggers_query).fetchall():
        on = t.on_name if t.on_schema == "public" else f"{t.on_schema}.{t.on_name}"
        execute = (
            t.execute_name
            if t.execute_schema == "public"
            else f"{t.execute_schema}.{t.execute_name}"
        )

        condition: str | None = None
        if t.when is not None:
            condition = t.when.lstrip("(").rstrip(")")
        trigger = Trigger(
            name=t.name,
            on=on,
            execute=execute,
            events=TriggerEvents.from_bit_string(t.type),
            time=TriggerTimes.from_bit_string(t.type),
            for_each=TriggerForEach.from_bit_string(t.type),
            condition=condition,
        )
        triggers.append(trigger)

    return triggers
