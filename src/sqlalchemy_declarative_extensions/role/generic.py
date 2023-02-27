from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Role:
    name: str

    in_roles: list[str] | None = None

    @classmethod
    def coerce_from_unknown(cls, unknown: str | Role) -> Role:
        if isinstance(unknown, Role):
            return replace(
                unknown, in_roles=sorted(unknown.in_roles) if unknown.in_roles else None
            )

        return cls(unknown)

    @property
    def has_option(self):
        return False

    @property
    def options(self):
        return []

    def to_sql_create(self) -> str:
        statement = f'CREATE ROLE "{self.name}"'
        if self.in_roles is not None:
            in_roles = ", ".join(self.in_roles)
            statement += f"IN ROLE {in_roles}"
        return statement + ";"

    def to_sql_update(self, to_role) -> list[str]:
        raise NotImplementedError(
            "When using the generic role, there should never exist any cause to update a role."
        )

    def to_sql_drop(self) -> str:
        return f'DROP ROLE "{self.name}";'
