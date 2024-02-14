from __future__ import annotations

from dataclasses import dataclass, field, fields
from datetime import datetime

from sqlalchemy_declarative_extensions.role import generic


class ValidUntilInifinty:
    """Sentinal value to indicate that the role's `valid_until` field is infinite.

    Using normal `ALTER ROLE` statements, setting `valid until` to `'infinity'` seems
    to be the canonical method, rather than being able to unset the value entirely.
    """


@dataclass(frozen=True)
class Role(generic.Role):
    """Define a role object.

    postgres: https://www.postgresql.org/docs/current/sql-createrole.html

    Note, the password field can be supplied, but it will be ignored when
    performing comparisons against existing roles. That is, changing the
    password field will not produce any (alembic) changes!

    Note, a `valid_until` value of `None` implies that it should never expire,
    this translates into no net-change to the role if there is no expiration set
    already, however it translates to 'infinity' if there is an expiration being
    removed.
    """

    superuser: bool | None = False
    createdb: bool | None = False
    createrole: bool | None = False
    inherit: bool | None = True
    login: bool | None = False
    replication: bool | None = False
    bypass_rls: bool | None = False
    connection_limit: int | None = None
    valid_until: datetime | None = None

    password: str | None = field(default=None, compare=False)

    @classmethod
    def from_pg_role(cls, r) -> Role:
        return cls(
            r.rolname,
            superuser=r.rolsuper,
            createdb=r.rolcreatedb,
            createrole=r.rolcreaterole,
            login=r.rolcanlogin,
            replication=r.rolreplication,
            connection_limit=r.rolconnlimit if r.rolconnlimit != -1 else None,
            bypass_rls=r.rolbypassrls,
            valid_until=r.rolvaliduntil,
            in_roles=sorted(r.memberof) if r.memberof else None,
        )

    @classmethod
    def from_unknown_role(cls, r: generic.Role | Role) -> Role:
        if not isinstance(r, Role):
            return Role(r.name, in_roles=sorted(r.in_roles) if r.in_roles else None)

        return r

    @property
    def options(self):
        for f in fields(self):
            if f.name == "name":
                continue

            value = getattr(self, f.name)
            if value is None:
                continue

            yield f.name, value

    def __repr__(self):
        cls_name = self.__class__.__name__
        options = ", ".join([f"{key}={value!r}" for key, value in self.options])
        return f'{cls_name}("{self.name}", {options})'

    def to_sql_create(self) -> str:
        segments = ["CREATE ROLE", self.name]

        options = postgres_render_role_options(self)
        if options:
            segments.append("WITH")
        segments.extend(options)

        if self.in_roles is not None:
            in_roles = ", ".join(self.in_roles)
            segment = f"IN ROLE {in_roles}"
            segments.append(segment)

        command = " ".join(segments)
        return command + ";"

    def to_sql_update(self, to_role: Role) -> list[str]:
        role_name = to_role.name
        diff = RoleDiff.diff(self, to_role)

        result = []

        diff_options = postgres_render_role_options(diff)
        if diff_options:
            segments = ["ALTER ROLE", role_name, "WITH", *diff_options]
            alter_role = " ".join(segments) + ";"
            result.append(alter_role)

        for add_name in diff.add_roles:
            result.append(f"GRANT {add_name} TO {role_name};")

        for remove_name in diff.remove_roles:
            result.append(f"REVOKE {remove_name} FROM {role_name};")

        return result


@dataclass
class RoleDiff:
    name: str
    superuser: bool | None = None
    createdb: bool | None = None
    createrole: bool | None = None
    inherit: bool | None = None
    login: bool | None = None
    replication: bool | None = None
    bypass_rls: bool | None = None
    connection_limit: int | None = None
    valid_until: datetime | ValidUntilInifinty | None = None

    add_roles: list[str] = field(default_factory=list)
    remove_roles: list[str] = field(default_factory=list)

    @classmethod
    def diff(cls, from_role: Role, to_role: Role) -> RoleDiff:
        superuser = None
        if to_role.superuser != from_role.superuser:
            superuser = to_role.superuser

        createdb = None
        if to_role.createdb != from_role.createdb:
            createdb = to_role.createdb

        createrole = None
        if to_role.createrole != from_role.createrole:
            createrole = to_role.createrole

        inherit = None
        if to_role.inherit != from_role.inherit:
            inherit = to_role.inherit

        login = None
        if to_role.login != from_role.login:
            login = to_role.login

        replication = None
        if to_role.replication != from_role.replication:
            replication = to_role.replication

        bypass_rls = None
        if to_role.bypass_rls != from_role.bypass_rls:
            bypass_rls = to_role.bypass_rls

        connection_limit = None
        if to_role.connection_limit != from_role.connection_limit:
            connection_limit = to_role.connection_limit

        valid_until: datetime | ValidUntilInifinty | None = None
        if to_role.valid_until != from_role.valid_until:
            if to_role.valid_until is None:
                valid_until = ValidUntilInifinty()
            else:
                valid_until = to_role.valid_until

        add_roles = []
        remove_roles = []
        if to_role.in_roles != from_role.in_roles:
            from_in_roles = from_role.in_roles or []
            to_in_roles = to_role.in_roles or []

            add_roles = [r for r in to_in_roles if r not in from_in_roles]
            remove_roles = [r for r in from_in_roles if r not in to_in_roles]

        return cls(
            name=to_role.name,
            superuser=superuser,
            createdb=createdb,
            createrole=createrole,
            inherit=inherit,
            login=login,
            replication=replication,
            bypass_rls=bypass_rls,
            connection_limit=connection_limit,
            valid_until=valid_until,
            add_roles=add_roles,
            remove_roles=remove_roles,
        )


def conditional_option(option, condition):
    if not condition:
        return f"NO{option}"
    return option


def postgres_render_role_options(role: Role | RoleDiff) -> list[str]:
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

    if isinstance(role, Role) and role.password is not None:
        segment = f"PASSWORD {role.password}"
        segments.append(segment)

    if role.valid_until is not None:
        if isinstance(role.valid_until, ValidUntilInifinty):
            timestamp = "infinity"
        else:
            timestamp = role.valid_until.isoformat()
        segment = f"VALID UNTIL '{timestamp}'"
        segments.append(segment)

    return segments
