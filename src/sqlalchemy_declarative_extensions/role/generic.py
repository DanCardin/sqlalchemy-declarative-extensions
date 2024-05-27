from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
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

    @property
    def has_option(self):
        return False

    @property
    def options(self):
        yield from []

    def normalize(self):
        return replace(
            self, in_roles=role_names(self.in_roles) if self.in_roles else None
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

    def to_sql_drop(self) -> str:
        return f'DROP ROLE "{self.name}";'


def by_name(r: Role | str) -> str:
    if isinstance(r, Role):
        return r.name
    return r


def role_names(roles: list[Role | str]) -> list[str]:
    return [r.name if isinstance(r, Role) else r for r in roles]
