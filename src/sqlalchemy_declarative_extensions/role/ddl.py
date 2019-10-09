from typing import List, Optional, Union

from sqlalchemy.engine import Connection
from sqlalchemy.schema import DDL, DDLElement, SchemaItem

from sqlalchemy_declarative_extensions.role import PGRole, PGRoleDiff, Role
from sqlalchemy_declarative_extensions.sqlalchemy import dialect_dispatch


def role_ddl(role: PGRole):
    ddl = DDL(postgres_render_create_role(role))
    return ddl.execute_if(callable_=check_role, state=role)  # type: ignore


def check_role(
    __ddl: DDLElement,
    __target: Optional[SchemaItem],
    connection: Connection,
    state,
    **_,
):
    existing_roles = identify_existing_roles(connection)
    role = state
    return role.name not in existing_roles


def identify_existing_roles_postgres(conn: Connection):
    select_roles = "SELECT rolname FROM pg_roles"
    return {
        role
        for role, *_ in conn.execute(select_roles).fetchall()
        if not role.startswith("pg_")
    }


identify_existing_roles = dialect_dispatch(
    postgresql=identify_existing_roles_postgres,
)


def conditional_option(option, condition):
    if not condition:
        option = f"NO{option}"
    return option


def postgres_render_create_role(role: PGRole) -> str:
    segments = ["CREATE ROLE", role.name]
    if role.has_option:
        segments.append("WITH")
        segments.extend(postgres_render_role_options(role))

    if role.in_roles is not None:
        in_roles = ", ".join(role.in_roles)
        segment = f"IN ROLE {in_roles}"
        segments.append(segment)

    command = " ".join(segments)
    return command


def postgres_render_update_role(from_role: PGRole, to_role: PGRole) -> List[DDL]:
    role_name = to_role.name
    diff = PGRoleDiff.diff(from_role, to_role)
    segments = ["ALTER ROLE", role_name, "WITH"]
    segments.extend(postgres_render_role_options(diff))
    alter = DDL(" ".join(segments))

    result = [alter]
    for add_name in diff.add_roles:
        result.append(DDL(f"GRANT {add_name} to {role_name}"))

    for remove_name in diff.remove_roles:
        result.append(DDL(f"GRANT {remove_name} to {role_name}"))

    return result


def postgres_render_drop_role(role: Role) -> DDL:
    return DDL(f"DROP ROLE {role.name}")


def postgres_render_role_options(role: Union[PGRole, PGRoleDiff]) -> List[str]:
    segments = []

    if role.superuser is not None:
        segment = conditional_option("SUPERUSER", role.superuser)
        segments.append(segment)

    if role.createdb is not None:
        segment = conditional_option("CREATEDB", role.createdb)
        segments.append(segment)

    if role.createrole is not None:
        segment = conditional_option("CREATEROLE", role.createrole)
        segments.append(segment)

    if role.inherit is not None:
        segment = conditional_option("INHERIT", role.inherit)
        segments.append(segment)

    if role.login is not None:
        segment = conditional_option("LOGIN", role.login)
        segments.append(segment)

    if role.replication is not None:
        segment = conditional_option("REPLICATION", role.replication)
        segments.append(segment)

    if role.bypass_rls is not None:
        segment = conditional_option("BYPASSRLS", role.bypass_rls)
        segments.append(segment)

    if role.connection_limit is not None:
        segment = f"CONNECTION LIMIT {role.connection_limit}"
        segments.append(segment)

    if isinstance(role, PGRole) and role.password is not None:
        segment = f"PASSWORD {role.password}"
        segments.append(segment)

    if role.valid_until is not None:
        timestamp = role.valid_until.isoformat()
        segment = f"VALID UNTIL '{timestamp}'"
        segments.append(segment)

    return segments
