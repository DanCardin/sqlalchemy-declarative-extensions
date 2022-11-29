from sqlalchemy_declarative_extensions.dialects import postgresql
from sqlalchemy_declarative_extensions.dialects.postgresql.query import (
    get_default_grants_postgresql,
    get_grants_postgresql,
    get_objects_postgresql,
    get_roles_postgresql,
)
from sqlalchemy_declarative_extensions.sqlalchemy import dialect_dispatch

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
