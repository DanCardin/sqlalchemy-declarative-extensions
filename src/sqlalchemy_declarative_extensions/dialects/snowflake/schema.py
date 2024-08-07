from __future__ import annotations

from dataclasses import dataclass

from typing_extensions import Self

from sqlalchemy_declarative_extensions.schema import base


@dataclass(order=True)
class Schema(base.Schema):
    """Represents a schema."""

    managed_access: bool = False

    @classmethod
    def coerce_from_unknown(cls, unknown: Self | str) -> Self:
        if isinstance(unknown, cls):
            return unknown

        if isinstance(unknown, base.Schema):
            return cls(unknown.name.upper())

        return cls(unknown)

    def to_sql_create(self) -> str:
        statement = str(super().to_sql_create())
        if self.managed_access:
            statement += " WITH MANAGED ACCESS"
        return statement + ";"
