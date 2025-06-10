from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from sqlalchemy.engine import Connection, Dialect
from typing_extensions import override

from sqlalchemy_declarative_extensions.view import base


@dataclass
class View(base.View):
    """Represent a snowflake specific view."""

    @classmethod
    @override
    def coerce_from_unknown(cls, unknown: Any) -> View:
        if isinstance(unknown, View):
            return unknown

        if isinstance(unknown, base.DeclarativeView):
            return cls(
                unknown.name.upper(),
                unknown.view_def,
                unknown.schema.upper() if unknown.schema else None,
            )

        result = super().coerce_from_unknown(unknown)

        return cls(
            name=result.name.upper(),
            definition=result.definition,
            schema=result.schema.upper() if result.schema else None,
        )

    def to_sql_create(self, dialect: Dialect | None = None) -> list[str]:
        definition = self.compile_definition(dialect).strip(";")

        components = ["CREATE"]

        components.append("VIEW")
        components.append(self.qualified_name)
        components.append("AS")
        components.append(definition)
        statement = " ".join(components) + ";"

        result = [statement]
        result.extend(self.render_constraints(create=True))

        return result

    def normalize(
        self,
        conn: Connection,
        naming_convention: base.NamingConvention | None,
        using_connection: bool = True,
    ) -> View:
        result = super().normalize(conn, naming_convention, using_connection)
        return replace(
            result,
            schema=self.schema.upper() if self.schema else None,
            name=self.name.upper(),
        )
