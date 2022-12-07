from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Callable, Container, Iterable, TypeVar, Union

from sqlalchemy import MetaData, column, select, table
from sqlalchemy.engine import Dialect
from sqlalchemy.sql import Select

from sqlalchemy_declarative_extensions.sql import qualify_name
from sqlalchemy_declarative_extensions.sqlalchemy import HasMetaData

try:
    from sqlalchemy.orm import DeclarativeMeta
except ImportError:  # pragma: no cover
    from sqlalchemy.ext.orm import DeclarativeMeta  # type: ignore

T = TypeVar("T", bound=Union[HasMetaData, MetaData])


_view_normal_translation = str.maketrans({" ": "", "\n": "", "\t": ""})


def view(base_or_metadata: T | None = None) -> Callable[[type], T]:
    """Decorate a class or declarative base model in order to register a View.

    Given some object with the attributes: `__tablename__`, (optionally for schema) `__table_args__`,
    and `__view__`, registers a View object.

    The `__view__` attribute can be either a raw string query, or a SQLAlchemy object
    capable of being compiled (namely :func:`~sqlalchemy.sql.expression.text` or :func:`~sqlalchemy.sql.expression.select`).

    This intentionally allows one to register a Model definition as a view,
    and have it register in the same way you might otherwise manually define it.
    This can be useful, to enable querying that view in native SQLAlchemy ORM-style,
    as though it were a table.

    >>> from sqlalchemy import Column, types
    >>> from sqlalchemy.orm import declarative_base
    >>> from sqlalchemy_declarative_extensions import view
    >>>
    >>> Base = declarative_base()
    >>>
    >>> @view()
    ... class Foo(Base):
    ...     __tablename__ = "foo"
    ...     __view__ = "SELECT * from bar"
    ...     id = Column(types.Integer, primary_key=True)

    Note that when doing this, alembic will still, by default, interpret the model
    definition as a Table and attempt to create it. As such, we expose an additional
    helper function :func:`~sqlalchemy_declarative_extensions.alembic.ignore_view_tables`,
    to simplify ignoring them.

    Alternatively, if you aren't intending to programmatically make use of the view,
    you can simply make a class object which resembles a table definition, but does
    not subclass `Base`. In this case, the `Base` or `MetaData` needs to be passed
    to the decorator.

    >>> from sqlalchemy.orm import declarative_base
    >>> from sqlalchemy_declarative_extensions import view
    >>>
    >>> Base = declarative_base()
    >>>
    >>> @view(Base)  # or Base.metadata
    ... class Foo:
    ...     __tablename__ = "foo"
    ...     __view__ = "SELECT * from bar"
    """

    def decorator(cls):
        nonlocal base_or_metadata

        name = cls.__tablename__
        table_args = getattr(cls, "__table_args__", None)
        view_def = cls.__view__

        schema = find_schema(table_args)
        instance = View(name, view_def, schema=schema)

        # When the object itself is a subclass of the declarative base,
        # the base can be omitted from the `view` input argument
        if isinstance(cls, DeclarativeMeta):
            base_or_metadata = cls

            cls.__table__.info["is_view"] = True
        else:
            # Otherwise, it's not, and we can apply some magic to allow
            # sqlalchemy to enable `pg.query(cls)`.
            def clause_element():
                return (
                    select(*[column(c.name) for c in view_def.selected_columns])
                    .select_from(table(instance.qualified_name))
                    .subquery()
                )

            cls.__clause_element__ = clause_element

        register_view(base_or_metadata, instance)

        return cls

    return decorator


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

    @classmethod
    def coerce_from_unknown(cls, unknown: Any) -> View:
        if isinstance(unknown, View):
            return unknown

        try:
            import alembic_utils  # noqa
        except ImportError:
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

    def render_definition(self, dialect: Dialect, *, normalize=False):
        if isinstance(self.definition, str):
            definition = self.definition
        else:
            definition = str(
                self.definition.compile(
                    dialect=dialect,
                    compile_kwargs={"literal_binds": True},
                )
            )

        if normalize:
            return definition.lower().translate(_view_normal_translation)

        return definition

    def equals(self, other: View, dialect: Dialect):
        same_view = (
            self.name == other.name
            and self.schema == other.schema
            and self.materialized == other.materialized
        )
        if not same_view:
            return False

        self_def = self.render_definition(dialect, normalize=True)
        other_def = other.render_definition(dialect, normalize=True)
        return self_def == other_def

    def to_sql_create(self, dialect: Dialect):
        definition = self.render_definition(dialect)

        components = ["CREATE"]
        if self.materialized:
            components.append("MATERIALIZED")

        components.append("VIEW")
        components.append(self.qualified_name)
        components.append("AS")
        components.append(definition)
        return " ".join(components)

    def to_sql_drop(self):
        components = ["DROP"]
        if self.materialized:
            components.append("MATERIALIZED")

        components.append("VIEW")
        components.append(self.qualified_name)
        return " ".join(components)


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
        for grant in self.grants:
            yield grant

    def are(self, *views: View):
        return replace(self, views=[View.coerce_from_unknown(v) for v in views])


def find_schema(table_args=None):
    if table_args is None:
        return None

    if isinstance(table_args, dict):
        return table_args.get("schema")

    if isinstance(table_args, Iterable):
        for table_arg in table_args:
            if isinstance(table_arg, dict):
                return table_arg.get("schema")
    return None
