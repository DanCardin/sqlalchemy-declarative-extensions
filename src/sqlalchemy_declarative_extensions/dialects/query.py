from sqlalchemy_declarative_extensions.dialects import postgresql
from sqlalchemy_declarative_extensions.dialects.postgresql.query import (
    check_schema_exists_postgresql,
    get_default_grants_postgresql,
    get_grants_postgresql,
    get_objects_postgresql,
    get_roles_postgresql,
    get_schemas_postgresql,
)
from sqlalchemy_declarative_extensions.dialects.sqlite.query import (
    check_schema_exists_sqlite,
)
from sqlalchemy_declarative_extensions.sqlalchemy import dialect_dispatch

get_schemas = dialect_dispatch(
    postgresql=get_schemas_postgresql,
)

check_schema_exists = dialect_dispatch(
    postgresql=check_schema_exists_postgresql,
    sqlite=check_schema_exists_sqlite,
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
