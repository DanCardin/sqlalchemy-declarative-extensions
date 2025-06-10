from __future__ import annotations

import inspect
import uuid
import warnings
from dataclasses import dataclass, field, replace
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    TypeVar,
    cast,
    overload,
)

from sqlalchemy import Index, MetaData, UniqueConstraint, text
from sqlalchemy.engine import Connection, Dialect
from sqlalchemy.sql import Select
from sqlalchemy.sql.compiler import IdentifierPreparer
from sqlalchemy.sql.elements import conv
from sqlalchemy.sql.naming import ConventionDict
from sqlalchemy.sql.schema import DEFAULT_NAMING_CONVENTION
from typing_extensions import Self

from sqlalchemy_declarative_extensions.sql import qualify_name
from sqlalchemy_declarative_extensions.sqlalchemy import (
    HasMetaData,
    create_mapper,
    escape_params,
)

if TYPE_CHECKING:
    from sqlalchemy_declarative_extensions.dialects.postgresql import (
        MaterializedOptions,
    )

T = TypeVar("T")
ViewType = TypeVar("ViewType", "View", "DeclarativeView")
NamingConvention = Dict[str, Any]


def view(
    base,
    *,
    register_as_model=False,
    materialized: bool | dict | MaterializedOptions = False,
) -> Callable[[T], T]:
    """Decorate a class or declarative base model in order to register a View.

    Given some object with the attributes: `__tablename__`, (optionally for schema) `__table_args__`,
    and `__view__`, registers a View object.

    The `__view__` attribute can be either a raw string query, a SQLAlchemy object
    capable of being compiled (namely :func:`~sqlalchemy.sql.expression.text` or
    :func:`~sqlalchemy.sql.expression.select`), or a no-argument function which returns
    either of the two.

    This intentionally allows one to register a Model definition as a view,
    and have it register in the same way you might otherwise manually define it.
    This can be useful, to enable querying that view in native SQLAlchemy ORM-style,
    as though it were a table.

    Arguments:
        base: A declarative base object
        register_as_model: Whether the view should be registered as a SQLAlchemy mapped object.
            Note this only works if the view defines mappable models columns (minimally a primary
            key), like a proper modeled table
        materialized: Whether a view should be materialized or not. Accepts a `bool` for default
            options, a dialect-specific `MaterializedOptions` variant, or a dict describing that
            dialect-specific variant.

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
    metadata = getattr(base, "metadata", None)
    if metadata is None:  # pragma: no cover
        raise ValueError("Model must have a 'metadata' attribute.")

    def decorator(cls):
        instance = DeclarativeView(cls, materialized)

        register_view(base, instance)

        if register_as_model:
            return instrument_sqlalchemy(base, cls)
        return cls

    return decorator


def instrument_sqlalchemy(base: T, cls) -> T:
    temp_metadata = MetaData(naming_convention=base.metadata.naming_convention)  # type: ignore
    return create_mapper(cls, temp_metadata)


def register_view(base_or_metadata: HasMetaData | MetaData, view: ViewType):
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


@dataclass
class DeclarativeView:
    cls: type
    materialized: bool | dict | MaterializedOptions

    @property
    def name(self):
        return self.cls.__tablename__

    @property
    def table_args(self):
        return getattr(self.cls, "__table_args__", None)

    @property
    def view_def(self):
        if inspect.isfunction(self.cls.__view__):
            return self.cls.__view__()

        return self.cls.__view__

    @property
    def schema(self):
        table_args = self.table_args
        if isinstance(table_args, dict):
            return table_args.get("schema")

        if isinstance(table_args, Iterable):
            for table_arg in table_args:
                if isinstance(table_arg, dict):
                    return table_arg.get("schema")

        return None

    @property
    def constraints(self):
        table_args = self.table_args
        if isinstance(table_args, dict):
            return None

        if isinstance(table_args, Iterable):
            return [
                arg
                for arg in table_args
                if isinstance(arg, (UniqueConstraint, ViewIndex, Index))
            ]

        return None


@dataclass
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
    materialized: bool | dict | MaterializedOptions = False
    constraints: list[Index | UniqueConstraint | ViewIndex] | None = field(default=None)

    @classmethod
    def coerce_from_unknown(cls, unknown: Any) -> View:
        if isinstance(unknown, View):
            if unknown.materialized or unknown.constraints:
                warnings.warn(
                    "`materialized` and `constraints` have been relocated to dialect-specific MaterializedView variants.",
                    DeprecationWarning,
                )

            return unknown

        if isinstance(unknown, DeclarativeView):
            return cls(unknown.name, unknown.view_def, unknown.schema)

        raise NotImplementedError(
            f"Unsupported view source object {unknown}"
        )  # pragma: no cover

    @property
    def qualified_name(self):
        return qualify_name(self.schema, self.name)

    def compile_definition(self, dialect: Dialect | None = None) -> str:
        if isinstance(self.definition, str):
            return self.definition

        return str(
            self.definition.compile(
                dialect=dialect,
                compile_kwargs={"literal_binds": True},
            )
        )

    def render_definition(self, conn: Connection, using_connection: bool = True):
        dialect = conn.engine.dialect

        compiled_definition = self.compile_definition(dialect)

        if using_connection and dialect.name == "postgresql":
            from sqlalchemy_declarative_extensions.dialects import get_view

            with conn.begin_nested() as trans:
                try:
                    random_name = "v" + uuid.uuid4().hex
                    conn.execute(
                        text(f"CREATE VIEW {random_name} AS {compiled_definition}")
                    )
                    view = get_view(conn, random_name)
                    definition1 = view.definition

                    # Optimization, the view query **can** change if we re-run it,
                    # but if it's not changed from the first iteration, we assume it won't.
                    if definition1 == compiled_definition:
                        return escape_params(compiled_definition)

                    # Re-generate the view, it **can** not produce the same text twice.
                    random_name = "v" + uuid.uuid4().hex
                    conn.execute(text(f"CREATE VIEW {random_name} AS {definition1}"))
                    view = get_view(conn, random_name)
                    definition2 = view.definition
                    return escape_params(definition2)
                finally:
                    trans.rollback()
        else:
            # Fall back to library-based normalization, which cannot be perfect.
            try:
                import sqlglot
                from sqlglot.optimizer.normalize import normalize
            except ImportError:  # pragma: no cover
                raise ImportError("View autogeneration requires the 'parse' extra.")

            dialect_name_map = {"postgresql": "postgres"}
            dialect_name = dialect_name_map.get(dialect.name, dialect.name)

            # aiosqlite, pmrsqlite, etc
            if "sqlite" in dialect_name:
                dialect_name = "sqlite"

            return (
                escape_params(
                    normalize(
                        sqlglot.parse_one(compiled_definition, read=dialect_name)
                    ).sql(dialect_name)
                )
                + ";"
            )

    def render_constraints(self, *, create):
        if not self.constraints:
            return []

        result = []
        for constraint in self.constraints:
            assert isinstance(constraint, ViewIndex)

            if create:
                query = constraint.create(self)
            else:
                query = constraint.drop(self)

            result.append(query)
        return result

    def normalize(
        self,
        conn: Connection,
        naming_convention: NamingConvention | None,
        using_connection: bool = True,
    ) -> Self:
        constraints = None
        if self.constraints:
            constraints = [
                ViewIndex.from_unknown(c, self, conn.dialect, naming_convention)
                for c in self.constraints
            ]

        return replace(
            self,
            definition=self.render_definition(conn, using_connection=using_connection),
            constraints=constraints,
        )

    def to_sql_create(self, dialect: Dialect | None = None) -> list[str]:
        assert self.materialized is False

        definition = self.compile_definition(dialect)

        components = ["CREATE", "VIEW", self.qualified_name, "AS", definition]
        statement = " ".join(components)

        result = [statement]
        result.extend(self.render_constraints(create=True))

        return result

    def to_sql_update(
        self, from_view: View, dialect: Dialect | None = None
    ) -> list[str]:
        result = []
        if (
            from_view.definition != self.definition
            or from_view.materialized != self.materialized
        ):
            result.extend(from_view.to_sql_drop(dialect))
            result.extend(self.to_sql_create(dialect))
        else:
            from_view_constraints = cast(
                Optional[List[ViewIndex]], from_view.constraints
            )
            constraints = cast(Optional[List[ViewIndex]], self.constraints)

            removed, missing = ViewIndex.diff(from_view_constraints, constraints)
            result.extend([c.drop(from_view) for c in removed])
            result.extend([c.create(self) for c in missing])

        return result

    def to_sql_drop(self, dialect: Dialect | None = None) -> list[str]:
        components = ["DROP"]
        if self.materialized:
            components.append("MATERIALIZED")

        components.append("VIEW")
        components.append(self.qualified_name)

        statement = " ".join(components)

        result = []
        result.extend(self.render_constraints(create=False))
        result.append(statement)

        return result


@dataclass
class ViewIndex:
    columns: list[str]
    name: str | None = None
    unique: bool = False

    @classmethod
    def from_unknown(
        cls,
        index: ViewIndex | Index | UniqueConstraint,
        source_view: View,
        dialect: Dialect,
        naming_convention: NamingConvention | None,
    ):
        if isinstance(index, ViewIndex):
            convention = "uq" if index.unique else "ix"
            instance = index
        elif isinstance(index, Index):
            convention = "ix"
            instance = ViewIndex(
                columns=cast(List[str], list(index.expressions)),
                name=index.name,
                unique=index.unique,
            )
        elif isinstance(index, UniqueConstraint):
            convention = "uq"
            instance = ViewIndex(
                columns=cast(List[str], list(index._pending_colargs)),
                name=str(index.name) if index.name else None,
                unique=True,
            )
        else:  # pragma: no cover
            raise NotImplementedError()

        if instance.name:
            return instance

        naming_convention = naming_convention or DEFAULT_NAMING_CONVENTION  # type: ignore
        assert naming_convention
        assert "ix" in naming_convention
        template = cast(
            str, naming_convention.get(convention) or naming_convention["ix"]
        )
        cd = ConventionDict(_ViewIndexAdapter(instance), source_view, naming_convention)
        conventionalized_name = conv(template % cd)

        try:
            name = IdentifierPreparer(dialect).truncate_and_render_index_name(
                conventionalized_name
            )
        except AttributeError:
            # SQLAlchemy < 1.4 does not have this function/behavior
            name = conventionalized_name

        return replace(instance, name=name)

    def create(self, on: View):
        on_name = qualify_name(on.schema, on.name, quote=True)
        unique = ""
        if self.unique:
            unique = " UNIQUE"

        columns = ", ".join(self.columns)
        return f'CREATE{unique} INDEX "{self.name}" ON {on_name} ({columns});'

    def drop(self, on: View):
        assert self.name
        name = qualify_name(on.schema, self.name, quote=True)
        return f"DROP INDEX {name};"

    @staticmethod
    def diff(
        existing_indices: list[ViewIndex] | None,
        declared_indices: list[ViewIndex] | None,
    ) -> tuple[list[ViewIndex], list[ViewIndex]]:
        removed = []
        missing = []

        existing_by_name = {x.name: x for x in existing_indices or []}
        declared_by_name = {x.name: x for x in declared_indices or []}

        for name, existing in existing_by_name.items():
            declared = declared_by_name.pop(name, None)
            if declared:
                # We need to replace ones which are declared but different in some way
                if existing != declared:
                    removed.append(existing)
                    missing.append(declared)
            else:
                # Whereas if they're not declared they should be removed.
                removed.append(existing)

        # The pop from above means anything left is automatically missing.
        for declared in declared_by_name.values():
            missing.append(declared)

        return (removed, missing)


@dataclass
class _ViewIndexAdapter:
    """Internal adapter type which stands in for the **actual** view index options.

    SQLAlchemy `Index` or `UniqueConstraint`, and local `ViewIndex` are the **actual**
    public view type options. However in order to make use of SQLAlchemy's internal
    naming convention logic, we need to pretend to be an object which acts like one
    of those internal types.

    This is also the purpose of `_ColumnNamingAdapter`
    """

    view_index: ViewIndex

    @property
    def name(self):
        return self.view_index.name

    @property
    def columns(self):
        return [_ColumnNamingAdapter(c) for c in self.view_index.columns]


@dataclass
class _ColumnNamingAdapter:
    name: str

    @property
    def _ddl_label(self):
        return self.name


@dataclass
class Views:
    """The collection of views and associated options comparisons.

    Note: `Views` supports views being specified from certain alternative sources, such
    as `alembic_utils`'s `PGView` and `PGMaterializedView`. In order for that to work,
    one needs to either call `View.coerce_from_unknown(alembic_utils_view)` directly, or
    use `Views().are(...)` (which internally calls `coerce_from_unknown`).

    Note: `ignore` option accepts a list of strings. Each string is individually
        interpreted as a "glob". This means a string like "foo.*" would ignore all views
        contained within the schema "foo".
    """

    views: list[View | DeclarativeView] = field(default_factory=list)

    ignore_unspecified: bool = False

    ignore: Iterable[str] = field(default_factory=set)
    ignore_views: Iterable[str] = field(default_factory=set)
    naming_convention: NamingConvention | None = None

    @classmethod
    def coerce_from_unknown(
        cls, unknown: None | Iterable[View] | Views
    ) -> Views | None:
        if isinstance(unknown, Views):
            return unknown

        if isinstance(unknown, Iterable):
            return cls().are(*unknown)

        return None

    @overload
    @classmethod
    def extract(cls, metadata: MetaData) -> Self: ...

    @overload
    @classmethod
    def extract(cls, metadata: list[MetaData]) -> Self: ...

    @overload
    @classmethod
    def extract(cls, metadata: list[MetaData | None]) -> Self | None: ...

    @overload
    @classmethod
    def extract(cls, metadata: None) -> None: ...

    @classmethod
    def extract(
        cls, metadata: MetaData | list[MetaData] | list[MetaData | None] | None
    ) -> Self | None:
        if not isinstance(metadata, Sequence):
            metadata = [metadata]

        naming_conventions = [m.naming_convention for m in metadata if m]
        instances: list[Self] = [
            m.info["views"] for m in metadata if m and m.info.get("views")
        ]

        instance_count = len(instances)
        if instance_count == 0:
            return None

        if not all(
            x.ignore_unspecified == instances[0].ignore_unspecified
            and x.naming_convention == instances[0].naming_convention
            for x in instances
        ):
            raise ValueError(
                "All combined `Views` instances must agree on the set of settings: ignore_unspecified, naming_convention"
            )

        views = [s for instance in instances for s in instance.views]
        ignore = [s for instance in instances for s in instance.ignore]
        ignore_views = [s for instance in instances for s in instance.ignore_views]

        ignore_unspecified = instances[0].ignore_unspecified
        naming_convention: NamingConvention = instances[0].naming_convention  # type: ignore

        if not naming_convention:
            if not all(n == naming_conventions[0] for n in naming_conventions):
                raise ValueError("All MetaData `naming_convention`s must agree")

            naming_convention = naming_conventions[0]  # type: ignore

        return cls(
            views=views,
            ignore_unspecified=ignore_unspecified,
            ignore=ignore,
            ignore_views=ignore_views,
            naming_convention=naming_convention,
        )

    def append(self, view: View | DeclarativeView):
        self.views.append(view)

    def __iter__(self):
        yield from self.views

    def are(self, *views: View):
        return replace(self, views=list(views))
