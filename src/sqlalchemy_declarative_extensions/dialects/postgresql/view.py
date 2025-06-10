from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Literal

from sqlalchemy.engine import Connection, Dialect
from typing_extensions import override

from sqlalchemy_declarative_extensions.view import base


@dataclass
class MaterializedOptions:
    with_data: bool = field(compare=False, default=True)

    @classmethod
    def from_value(
        cls, value: bool | dict | MaterializedOptions
    ) -> MaterializedOptions | Literal[False]:
        if not value:
            return False

        if value is True:
            return MaterializedOptions()

        if isinstance(value, dict):
            return MaterializedOptions(**value)

        return value


@dataclass
class View(base.View):
    """Represent a postgres-specific view.

    Per the deprecation on the base `View` object: There exists a `materialized`
    argument on this class, which has no effect on this class. It will be removed
    when the attribute is removed from the base class. The `constraints` field however,
    will remain, as this class is the new destination.
    """

    @classmethod
    @override
    def coerce_from_unknown(cls, unknown: Any) -> View:
        if isinstance(unknown, View):
            return unknown

        if isinstance(unknown, base.DeclarativeView):
            return cls(
                unknown.name,
                unknown.view_def,
                unknown.schema,
                materialized=unknown.materialized,
                constraints=unknown.constraints,
            )

        try:
            import alembic_utils  # noqa
        except ImportError:  # pragma: no cover
            pass
        else:
            from alembic_utils.pg_materialized_view import PGMaterializedView
            from alembic_utils.pg_view import PGView

            if isinstance(unknown, PGView):
                return cls(
                    name=unknown.signature,
                    definition=unknown.definition,
                    schema=unknown.schema,
                )

            if isinstance(unknown, PGMaterializedView):
                return cls(
                    name=unknown.signature,
                    definition=unknown.definition,
                    schema=unknown.schema,
                    materialized=MaterializedOptions(with_data=unknown.with_data),
                )

        result = super().coerce_from_unknown(unknown)
        if result.materialized:
            return cls(
                name=result.name,
                definition=result.definition,
                schema=result.schema,
                materialized=True,
                constraints=result.constraints,
            )

        return cls(
            name=result.name,
            definition=result.definition,
            schema=result.schema,
        )

    def to_sql_create(self, dialect: Dialect | None = None) -> list[str]:
        definition = self.compile_definition(dialect).strip(";")

        components = ["CREATE"]
        if self.materialized:
            components.append("MATERIALIZED")

        components.append("VIEW")
        components.append(self.qualified_name)
        components.append("AS")
        components.append(definition)

        materialized_options = MaterializedOptions.from_value(self.materialized)

        if self.materialized:
            assert isinstance(self.materialized, MaterializedOptions)
            if materialized_options and not materialized_options.with_data:
                components.append("WITH NO DATA")

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
        instance = super().normalize(conn, naming_convention, using_connection)
        return replace(
            instance,
            materialized=MaterializedOptions.from_value(self.materialized),
        )
