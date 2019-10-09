from __future__ import annotations

from dataclasses import astuple, dataclass, field, fields, replace
from datetime import datetime
from typing import Generic, Iterable, List, Optional, TypeVar, Union


@dataclass(frozen=True)
class Role:
    name: str

    in_roles: Optional[List[str]] = None

    @classmethod
    def coerce_from_unknown(cls, unknown: Union[str, Role]) -> Role:
        if isinstance(unknown, Role):
            return unknown

        return cls(unknown)

    @property
    def has_option(self):
        return False

    @property
    def options(self):
        return []


@dataclass(frozen=True)
class PGRole(Role):
    """Define a role object.

    postgres: https://www.postgresql.org/docs/current/sql-createrole.html
    """

    superuser: Optional[bool] = False
    createdb: Optional[bool] = False
    createrole: Optional[bool] = False
    inherit: Optional[bool] = True
    login: Optional[bool] = False
    replication: Optional[bool] = False
    bypass_rls: Optional[bool] = False
    connection_limit: Optional[int] = None
    valid_until: Optional[datetime] = None

    password: Optional[str] = field(default=None, compare=False)

    @classmethod
    def from_pg_role(cls, r) -> PGRole:
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
            in_roles=r.memberof or None,
        )

    @property
    def has_option(self):
        _, *options = astuple(self)
        return any(o is not None for o in options)

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
        options = ", ".join([f"{key}={repr(value)}" for key, value in self.options])
        return f'{cls_name}("{self.name}", {options})'


@dataclass
class PGRoleDiff:
    name: str
    superuser: Optional[bool] = None
    createdb: Optional[bool] = None
    createrole: Optional[bool] = None
    inherit: Optional[bool] = None
    login: Optional[bool] = None
    replication: Optional[bool] = None
    bypass_rls: Optional[bool] = None
    connection_limit: Optional[int] = None
    valid_until: Optional[datetime] = None

    add_roles: List[str] = field(default_factory=list)
    remove_roles: List[str] = field(default_factory=list)

    @classmethod
    def diff(cls, from_role: PGRole, to_role: PGRole) -> PGRoleDiff:
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

        valid_until = None
        if to_role.valid_until != from_role.valid_until:
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


R = TypeVar("R", PGRole, Role)
R_unknown = Union[PGRole, Role, str]


@dataclass
class Roles(Generic[R]):
    roles: List[R] = field(default_factory=list)
    ignore_unspecified: bool = False
    ignore_roles: List[str] = field(default_factory=list)

    @classmethod
    def coerce_from_unknown(
        cls, unknown: Union[None, Iterable[R_unknown], Roles]
    ) -> Optional[Roles]:
        if isinstance(unknown, Roles):
            return unknown

        if isinstance(unknown, Iterable):
            return Roles().are(*unknown)

        return None

    def __iter__(self):
        for role in self.roles:
            yield role

    def are(self, *roles: R_unknown):
        return replace(
            self,
            roles=[Role.coerce_from_unknown(role) for role in roles],
        )
