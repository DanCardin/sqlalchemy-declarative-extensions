from __future__ import annotations

from collections.abc import Callable
from typing import Type, TypeVar, cast

from sqlalchemy import func
from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions.dialects import mysql, postgresql, snowflake
from sqlalchemy_declarative_extensions.dialects.mysql.query import (
    check_schema_exists_mysql,
    get_functions_mysql,
    get_procedures_mysql,
    get_triggers_mysql,
    get_views_mysql,
)
from sqlalchemy_declarative_extensions.dialects.postgresql.query import (
    check_schema_exists_postgresql,
    get_databases_postgresql,
    get_default_grants_postgresql,
    get_functions_postgresql,
    get_grants_postgresql,
    get_objects_postgresql,
    get_procedures_postgresql,
    get_roles_postgresql,
    get_schemas_postgresql,
    get_triggers_postgresql,
    get_view_postgresql,
    get_views_postgresql,
)
from sqlalchemy_declarative_extensions.dialects.snowflake.query import (
    check_schema_exists_snowflake,
    get_databases_snowflake,
    get_roles_snowflake,
    get_schemas_snowflake,
    get_views_snowflake,
)
from sqlalchemy_declarative_extensions.dialects.sqlite.query import (
    check_schema_exists_sqlite,
    get_schemas_sqlite,
    get_views_sqlite,
)
from sqlalchemy_declarative_extensions.function.base import Function
from sqlalchemy_declarative_extensions.procedure import Procedure
from sqlalchemy_declarative_extensions.role import Role
from sqlalchemy_declarative_extensions.schema.base import Schema
from sqlalchemy_declarative_extensions.sqlalchemy import dialect_dispatch, select
from sqlalchemy_declarative_extensions.view import View

A = TypeVar("A")
T = TypeVar("T")


def get_cls(t: type[T], _: type[A]) -> Callable[[Connection], type[A]]:
    def wrapper(_: Connection) -> type[A]:
        return cast(Type[A], t)

    return wrapper


get_schemas = dialect_dispatch(
    postgresql=get_schemas_postgresql,
    sqlite=get_schemas_sqlite,
    snowflake=get_schemas_snowflake,
)

get_schema_cls = dialect_dispatch(
    default=get_cls(Schema, Schema),
    snowflake=get_cls(snowflake.Schema, Schema),
)

check_schema_exists = dialect_dispatch(
    postgresql=check_schema_exists_postgresql,
    sqlite=check_schema_exists_sqlite,
    mysql=check_schema_exists_mysql,
    snowflake=check_schema_exists_snowflake,
)

get_objects = dialect_dispatch(
    postgresql=get_objects_postgresql,
)

get_databases = dialect_dispatch(
    postgresql=get_databases_postgresql,
    snowflake=get_databases_snowflake,
)

get_default_grants = dialect_dispatch(
    postgresql=get_default_grants_postgresql,
)

get_grants = dialect_dispatch(
    postgresql=get_grants_postgresql,
)

get_roles = dialect_dispatch(
    postgresql=get_roles_postgresql,
)

get_roles = dialect_dispatch(
    postgresql=get_roles_postgresql,
    snowflake=get_roles_snowflake,
)

get_role_cls = dialect_dispatch(
    postgresql=get_cls(postgresql.Role, Role),
    snowflake=get_cls(snowflake.Role, Role),
    sqlite=get_cls(Role, Role),
)

get_views = dialect_dispatch(
    postgresql=get_views_postgresql,
    sqlite=get_views_sqlite,
    mysql=get_views_mysql,
    snowflake=get_views_snowflake,
)

get_view_cls = dialect_dispatch(
    postgresql=get_cls(postgresql.View, View),
    snowflake=get_cls(snowflake.View, View),
    default=get_cls(View, View),
)

get_view = dialect_dispatch(
    postgresql=get_view_postgresql,
)

get_procedures = dialect_dispatch(
    postgresql=get_procedures_postgresql,
    mysql=get_procedures_mysql,
)

get_procedure_cls = dialect_dispatch(
    postgresql=get_cls(postgresql.Procedure, Procedure),
    mysql=get_cls(mysql.Procedure, Procedure),
)

get_functions = dialect_dispatch(
    postgresql=get_functions_postgresql,
    mysql=get_functions_mysql,
)

get_function_cls = dialect_dispatch(
    postgresql=get_cls(postgresql.Function, Function),
    mysql=get_cls(mysql.Function, Function),
)

get_triggers = dialect_dispatch(
    postgresql=get_triggers_postgresql,
    mysql=get_triggers_mysql,
)


def check_table_exists(
    connection: Connection, tablename: str, schema: str | None = None
):
    return connection.dialect.has_table(connection, tablename, schema=schema)


def get_current_schema(connection: Connection) -> str | None:
    if connection.dialect.name == "mysql":
        return None

    schema = connection.execute(select(func.current_schema())).scalar()

    default_schema = connection.dialect.default_schema_name
    if not schema or schema == default_schema:
        return None

    return schema.lower()
