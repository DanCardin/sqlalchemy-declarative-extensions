from __future__ import annotations

import os
from dataclasses import dataclass, replace
from typing import Sequence

from sqlalchemy_declarative_extensions.context import context

__all__ = [
    "Role",
    "Env",
]


@dataclass(order=True)
class Role:
    """Represent a role.

    Note a role can be defined as "external=True" so that it can be used in downstream
    DDL, without requiring that it be managed within the context of the library.

    >>> base = Role("base", external=True)  # i.e. assumed to already exist, will not be created/updated
    >>> foo = Role("base", in_roles=[base])
    """

    name: str

    in_roles: list[Role | str] | None = None
    external: bool = False

    use_role: Role | str | None = None

    def __post_init__(self):
        if self.use_role:
            return

        use_role = context.role
        if use_role:
            self.use_role = use_role

    @classmethod
    def coerce_from_unknown(cls, unknown: str | Role) -> Role:
        if isinstance(unknown, Role):
            return replace(
                unknown,
                in_roles=sorted(unknown.in_roles, key=by_name)
                if unknown.in_roles
                else None,
            )

        return cls(unknown)

    @classmethod
    def from_unknown_role(cls, r: Role) -> Role:
        return cls(
            r.name,
            in_roles=r.in_roles,
            external=r.external,
            use_role=r.use_role,
        )

    @property
    def has_option(self):
        return False

    @property
    def is_dynamic(self) -> bool:
        return False

    @property
    def options(self):
        yield from []

    def normalize(self):
        return replace(
            self,
            in_roles=role_names(self.in_roles) if self.in_roles else None,
            use_role=role_name(self.use_role) if self.use_role else None,
        )

    def to_sql_create(self, raw: bool = True) -> list[str]:
        statement = f"CREATE ROLE {quote_name(self.name)}"
        if self.in_roles is not None:
            statement += f"IN ROLE {quote_names(self.in_roles)}"
        return [statement + ";"]

    def to_sql_update(self, to_role, raw: bool = True) -> list[str]:
        raise NotImplementedError(
            "When using the generic role, there should never exist any cause to update a role."
        )

    def to_sql_drop(self, raw: bool = True) -> list[str]:
        return [f"DROP ROLE {quote_name(self.name)};"]

    def to_sql_use(self, undo: bool) -> list[str]:
        raise NotImplementedError()

    def __enter__(self):
        context.enter_role(self)

    def __exit__(self, *_):
        context.exit_role()


@dataclass
class Env:
    """Provide a way to supply dynamic password variables through the environment at migration time."""

    name: str
    default: str | None = None

    def resolve(self, raw: bool = False):
        if raw:
            if self.default is not None:
                return os.environ.get(self.name, self.default)
            return os.environ[self.name]

        if self.default is not None:
            return f'{{os.environ.get("{self.name}", "{self.default}")}}'
        return f'{{os.environ["{self.name}"]}}'


def by_name(r: Role | str) -> str:
    if isinstance(r, Role):
        return r.name
    return r


def role_name(role: Role | str) -> str:
    return role.name if isinstance(role, Role) else role


def role_names(roles: list[Role | str]) -> list[str]:
    return [role_name(r) for r in roles]


def quote_name(role: Role | str) -> str:
    return f'"{role_name(role)}"'


def quote_names(roles: Sequence[Role | str]) -> str:
    return ", ".join(quote_name(role) for role in roles)
