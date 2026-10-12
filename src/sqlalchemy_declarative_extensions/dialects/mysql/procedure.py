from __future__ import annotations

import enum
import textwrap
from dataclasses import dataclass, replace

from typing_extensions import Self

from sqlalchemy_declarative_extensions.dialects.from_string import FromStrings
from sqlalchemy_declarative_extensions.procedure import base


@enum.unique
class ProcedureSecurity(FromStrings):
    invoker = "INVOKER"
    definer = "DEFINER"


@dataclass
class Procedure(base.Procedure):
    """Describes a MySQL procedure."""

    security: ProcedureSecurity = ProcedureSecurity.definer

    def __post_init__(self):
        self.security = ProcedureSecurity.from_string(self.security)

    @classmethod
    def from_unknown_procedure(cls, f: base.Procedure) -> Self:
        if isinstance(f, cls):
            return f

        return cls(
            name=f.name,
            definition=f.definition,
            schema=f.schema,
        )

    def with_security(self, security: ProcedureSecurity | str):
        return replace(self, security=ProcedureSecurity.from_string(security))

    def with_security_definer(self):
        return replace(self, security=ProcedureSecurity.definer)

    def to_sql_create(self) -> list[str]:
        components = ["CREATE"]

        components.append("PROCEDURE")
        components.append(self.qualified_name + "()")

        if self.security == ProcedureSecurity.invoker:
            components.append("SQL SECURITY INVOKER")

        components.append(self.definition)

        return [" ".join(components) + ";"]

    def to_sql_drop(self) -> list[str]:
        return [f"DROP PROCEDURE {self.qualified_name};"]

    def normalize(self) -> Self:
        """Normalize the procedure definition by dedenting and normalize the SQL."""
        definition = textwrap.dedent(self.definition).strip().strip(";")
        return replace(self, definition=definition)
