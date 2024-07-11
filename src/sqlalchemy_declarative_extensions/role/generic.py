from __future__ import annotations

from dataclasses import dataclass, replace

from sqlalchemy_declarative_extensions.context import context


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
    def options(self):
        yield from []

    def normalize(self):
        return replace(
            self,
            in_roles=role_names(self.in_roles) if self.in_roles else None,
            use_role=role_name(self.use_role) if self.use_role else None,
        )

    def to_sql_create(self) -> list[str]:
        statement = f'CREATE ROLE "{self.name}"'
        if self.in_roles is not None:
            in_roles = ", ".join(role_names(self.in_roles))
            statement += f"IN ROLE {in_roles}"
        return [statement + ";"]

    def to_sql_update(self, to_role) -> list[str]:
        raise NotImplementedError(
            "When using the generic role, there should never exist any cause to update a role."
        )

    def to_sql_drop(self) -> list[str]:
        return [f'DROP ROLE "{self.name}";']

    def to_sql_use(self, undo: bool) -> list[str]:
        raise NotImplementedError()

    def __enter__(self):
        context.enter_role(self)

    def __exit__(self, *_):
        context.exit_role()


def by_name(r: Role | str) -> str:
    if isinstance(r, Role):
        return r.name
    return r


def role_name(role: Role | str) -> str:
    return role.name if isinstance(role, Role) else role


def role_names(roles: list[Role | str]) -> list[str]:
    return [role_name(r) for r in roles]
