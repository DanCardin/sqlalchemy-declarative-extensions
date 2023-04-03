from sqlalchemy_declarative_extensions.dialects import postgresql
from sqlalchemy_declarative_extensions.dialects.mysql.query import (
    check_schema_exists_mysql,
    check_table_exists_mysql,
    get_views_mysql,
)
from sqlalchemy_declarative_extensions.dialects.postgresql.query import (
    check_schema_exists_postgresql,
    check_table_exists_postgresql,
    get_default_grants_postgresql,
    get_functions_postgresql,
    get_grants_postgresql,
    get_objects_postgresql,
    get_roles_postgresql,
    get_schemas_postgresql,
    get_triggers_postgresql,
    get_view_postgresql,
    get_views_postgresql,
)
from sqlalchemy_declarative_extensions.dialects.sqlite.query import (
    check_schema_exists_sqlite,
    check_table_exists_sqlite,
    get_views_sqlite,
)
from sqlalchemy_declarative_extensions.sqlalchemy import dialect_dispatch

get_schemas = dialect_dispatch(
    postgresql=get_schemas_postgresql,
)

check_schema_exists = dialect_dispatch(
    postgresql=check_schema_exists_postgresql,
    sqlite=check_schema_exists_sqlite,
    mysql=check_schema_exists_mysql,
)

check_table_exists = dialect_dispatch(
    postgresql=check_table_exists_postgresql,
    sqlite=check_table_exists_sqlite,
    mysql=check_table_exists_mysql,
)

get_objects = dialect_dispatch(
    postgresql=get_objects_postgresql,
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
)

get_role_cls = dialect_dispatch(
    postgresql=lambda _: postgresql.Role,
)

get_views = dialect_dispatch(
    postgresql=get_views_postgresql,
    sqlite=get_views_sqlite,
    mysql=get_views_mysql,
)

get_view = dialect_dispatch(
    postgresql=get_view_postgresql,
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
