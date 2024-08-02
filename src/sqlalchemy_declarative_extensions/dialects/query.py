from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions.dialects import postgresql, snowflake
from sqlalchemy_declarative_extensions.dialects.mysql.query import (
    check_schema_exists_mysql,
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
    get_objects_snowflake,
    get_default_grants_snowflake,
    get_grants_snowflake,
)
from sqlalchemy_declarative_extensions.dialects.sqlite.query import (
    check_schema_exists_sqlite,
    get_schemas_sqlite,
    get_views_sqlite,
)
from sqlalchemy_declarative_extensions.role import Role
from sqlalchemy_declarative_extensions.sqlalchemy import dialect_dispatch, select
from sqlalchemy_declarative_extensions.view import View

get_schemas = dialect_dispatch(
    postgresql=get_schemas_postgresql,
    sqlite=get_schemas_sqlite,
    snowflake=get_schemas_snowflake,
)

check_schema_exists = dialect_dispatch(
    postgresql=check_schema_exists_postgresql,
    sqlite=check_schema_exists_sqlite,
    mysql=check_schema_exists_mysql,
    snowflake=check_schema_exists_snowflake,
)

get_objects = dialect_dispatch(
    postgresql=get_objects_postgresql,
    snowflake=get_objects_snowflake,
)

get_databases = dialect_dispatch(
    postgresql=get_databases_postgresql,
    snowflake=get_databases_snowflake,
)

get_default_grants = dialect_dispatch(
    postgresql=get_default_grants_postgresql,
    snowflake=get_default_grants_snowflake,
)

get_grants = dialect_dispatch(
    postgresql=get_grants_postgresql,
    snowflake=get_grants_snowflake,
)

get_grant_cls = dialect_dispatch(
    postgresql=lambda _: postgresql.GrantStatement,
    snowflake=lambda _: snowflake.GrantStatement,
)

get_default_grant_cls = dialect_dispatch(
    postgresql=lambda _: postgresql.DefaultGrantStatement,
    snowflake=lambda _: snowflake.DefaultGrantStatement,
)

get_roles = dialect_dispatch(
    postgresql=get_roles_postgresql,
    snowflake=get_roles_snowflake,
)

get_role_cls = dialect_dispatch(
    postgresql=lambda _: postgresql.Role,
    snowflake=lambda _: snowflake.Role,
    sqlite=lambda _: Role,
)

get_views = dialect_dispatch(
    postgresql=get_views_postgresql,
    sqlite=get_views_sqlite,
    mysql=get_views_mysql,
)

get_view_cls = dialect_dispatch(
    postgresql=lambda _: postgresql.View,
    default=lambda _: View,
)

get_view = dialect_dispatch(
    postgresql=get_view_postgresql,
)

get_procedures = dialect_dispatch(
    postgresql=get_procedures_postgresql,
)

get_procedure_cls = dialect_dispatch(
    postgresql=lambda _: postgresql.Procedure,
)

get_functions = dialect_dispatch(
    postgresql=get_functions_postgresql,
)

get_function_cls = dialect_dispatch(
    postgresql=lambda _: postgresql.Function,
)

get_triggers = dialect_dispatch(
    postgresql=get_triggers_postgresql,
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
