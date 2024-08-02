from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.sql.base import Executable
from sqlalchemy.sql.ddl import CreateSchema
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
            return cls(unknown.name)

        return cls(unknown)

    def to_sql_create(self) -> Executable | str:
        statement = super().to_sql_create()
        assert isinstance(statement, CreateSchema)

        result = statement.element
        if self.managed_access:
            result += " WITH MANAGED ACCESS"
        return result
