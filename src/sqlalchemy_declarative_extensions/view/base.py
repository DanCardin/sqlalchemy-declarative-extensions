from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Callable, Container, Iterable, TypeVar

import sqlalchemy.exc
from sqlalchemy import Index, MetaData
from sqlalchemy.engine import Dialect
from sqlalchemy.schema import CreateIndex, DropIndex
from sqlalchemy.sql import Select

from sqlalchemy_declarative_extensions.sql import qualify_name
from sqlalchemy_declarative_extensions.sqlalchemy import HasMetaData, create_mapper

T = TypeVar("T", bound=HasMetaData)


def view(base: T, materialized: bool = False) -> Callable[[type], T]:
    """Decorate a class or declarative base model in order to register a View.

    Given some object with the attributes: `__tablename__`, (optionally for schema) `__table_args__`,
    and `__view__`, registers a View object.

    The `__view__` attribute can be either a raw string query, or a SQLAlchemy object
    capable of being compiled (namely :func:`~sqlalchemy.sql.expression.text` or :func:`~sqlalchemy.sql.expression.select`).

    This intentionally allows one to register a Model definition as a view,
    and have it register in the same way you might otherwise manually define it.
    This can be useful, to enable querying that view in native SQLAlchemy ORM-style,
    as though it were a table.

    >>> try:
    ...     from sqlalchemy.orm import declarative_base
    ... except ImportError:
    ...     from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base
    >>> from sqlalchemy import Column, types
    >>> from sqlalchemy_declarative_extensions import view
    >>>
    >>> Base = declarative_base()
    >>>
    >>> @view(Base)
    ... class Foo:
    ...     __tablename__ = "foo"
    ...     __view__ = "SELECT * from bar"
    ...
    ...     id = Column(types.Integer, primary_key=True)
    """

    def decorator(cls):
        name = cls.__tablename__
        table_args = getattr(cls, "__table_args__", None)
        view_def = cls.__view__

        schema = find_schema(table_args)
        constraints = find_constraints(table_args)
        instance = View(
            name,
            view_def,
            schema=schema,
            materialized=materialized,
            constraints=constraints,
        )

        register_view(base, instance)

        return instrument_sqlalchemy(base, cls)

    return decorator


def instrument_sqlalchemy(base: T, cls) -> T:
    temp_metadata = MetaData(naming_convention=base.metadata.naming_convention)
    try:
        mapper = create_mapper(cls, temp_metadata)
    except sqlalchemy.exc.ArgumentError:
        mapper = cls

    return mapper


def register_view(base_or_metadata: HasMetaData | MetaData, view: View):
    """Register a view onto the given declarative base or `Metadata`.

    This can be used instead of the [view](view) decorator, if you are constructing
    `View` objects directly. In this way, you can imperitively register views next
    to their corresponding table definitions, rather than at the root declarative
    base, like many of the other object types are documented to do.
    """
    if isinstance(base_or_metadata, MetaData):
        metadata = base_or_metadata
    else:
        metadata = base_or_metadata.metadata

    if not metadata.info.get("views"):
        metadata.info["views"] = Views()
    metadata.info["views"].append(view)


@dataclass(eq=False)
class View:
    """Definition of a view.

    **Note** the `materialized` field will always be false for databases
    which don't support it, and may generate invalid SQL if declared when
    unsupported.

    Note in order to register a View, it must be directly included on the declarative
    base/metadata `Views` object, called with `register_view`, or produced by
    a `view` decorator.
    """

    name: str
    definition: str | Select
    schema: str | None = None
    materialized: bool = False
    constraints: list[Index] | None = None

    @classmethod
    def coerce_from_unknown(cls, unknown: Any) -> View:
        if isinstance(unknown, View):
            return unknown

        try:
            import alembic_utils  # noqa
        except ImportError:  # pragma: no cover
            pass
        else:
            from alembic_utils.pg_materialized_view import PGMaterializedView
            from alembic_utils.pg_view import PGView

            if isinstance(unknown, (PGView, PGMaterializedView)):
                materialized = isinstance(unknown, PGMaterializedView)
                return cls(
                    name=unknown.signature,
                    definition=unknown.definition,
                    schema=unknown.schema,
                    materialized=materialized,
                )

        raise NotImplementedError(  # pragma: no cover
            f"Unsupported view source object {unknown}"
        )

    @property
    def qualified_name(self):
        return qualify_name(self.schema, self.name)

    def render_definition(self, dialect: Dialect):
        try:
            import sqlglot
            from sqlglot.optimizer.normalize import normalize
        except ImportError:  # pragma: no cover
            raise ImportError("View autogeneration requires the 'parse' extra.")

        if isinstance(self.definition, str):
            definition = self.definition
        else:
            definition = str(
                self.definition.compile(
                    dialect=dialect,
                    compile_kwargs={"literal_binds": True},
                )
            )

        dialect_name_map = {"postgresql": "postgres"}
        dialect_name = dialect_name_map.get(dialect.name, dialect.name)
        return normalize(sqlglot.parse_one(definition, read=dialect_name)).sql() + ";"

    def render_constraints(self, dialect, *, create):
        if not self.constraints:
            return []

        if create:
            action = CreateIndex
        else:
            action = DropIndex

        return [
            str(action(constraint).compile(dialect=dialect)).replace("\n", "")
            for constraint in self.constraints
        ]

    def equals(self, other: View, dialect: Dialect):
        same_view = (
            self.name == other.name
            and self.schema == other.schema
            and self.materialized == other.materialized
        )
        if not same_view:
            return False

        self_def = self.render_definition(dialect)
        other_def = other.render_definition(dialect)

        return self_def == other_def

    def to_sql_create(self, dialect: Dialect) -> list[str]:
        definition = self.render_definition(dialect)

        components = ["CREATE"]
        if self.materialized:
            components.append("MATERIALIZED")

        components.append("VIEW")
        components.append(self.qualified_name)
        components.append("AS")
        components.append(definition)
        statement = " ".join(components)

        result = [statement]
        result.extend(self.render_constraints(dialect, create=True))

        return result

    def to_sql_drop(self, dialect: Dialect) -> list[str]:
        components = ["DROP"]
        if self.materialized:
            components.append("MATERIALIZED")

        components.append("VIEW")
        components.append(self.qualified_name)

        statement = " ".join(components)

        result = [statement]
        result.extend(self.render_constraints(dialect, create=False))

        return result


@dataclass
class Views:
    """The collection of views and associated options comparisons.

    Note, `Views` supports views being specified from certain alternative sources, such
    as `alembic_utils`'s `PGView` and `PGMaterializedView`. In order for that to work,
    one needs to either call `View.coerce_from_unknown(alembic_utils_view)` directly, or
    use `Views().are(...)` (which internally calls `coerce_from_unknown`).
    """

    views: list[View] = field(default_factory=list)

    ignore_unspecified: bool = False
    ignore_views: Container[str] = field(default_factory=set)

    @classmethod
    def coerce_from_unknown(
        cls, unknown: None | Iterable[View] | Views
    ) -> Views | None:
        if isinstance(unknown, Views):
            return unknown

        if isinstance(unknown, Iterable):
            return cls().are(*unknown)

        return None

    def append(self, view: View):
        self.views.append(view)

    def __iter__(self):
        for view in self.views:
            yield view

    def are(self, *views: View):
        return replace(self, views=[View.coerce_from_unknown(v) for v in views])


def find_schema(table_args=None):
    if isinstance(table_args, dict):
        return table_args.get("schema")

    if isinstance(table_args, Iterable):
        for table_arg in table_args:
            if isinstance(table_arg, dict):
                return table_arg.get("schema")

    return None


def find_constraints(table_args=None):
    if isinstance(table_args, dict):
        return None

    if isinstance(table_args, Iterable):
        return [table_arg for table_arg in table_args if isinstance(table_arg, Index)]

    return None
