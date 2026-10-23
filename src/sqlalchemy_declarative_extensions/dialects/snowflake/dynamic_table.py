from __future__ import annotations

import inspect
from dataclasses import dataclass, field, replace
from fnmatch import fnmatch
from typing import Any, Callable, Iterable, Sequence, TypeVar, Union

from sqlalchemy import MetaData, text
from sqlalchemy.engine import Connection, Dialect
from sqlalchemy.sql import Select
from typing_extensions import Self

from sqlalchemy_declarative_extensions.op import ExecuteOp
from sqlalchemy_declarative_extensions.sql import match_name, qualify_name
from sqlalchemy_declarative_extensions.sqlalchemy import HasMetaData, escape_params

T = TypeVar("T")


def dynamic_table(
    base,
    *,
    target_lag: str,
    warehouse: str,
) -> Callable[[T], T]:
    """Decorate a class to register a Snowflake Dynamic Table.

    Given an object with ``__tablename__``, optionally ``__table_args__``,
    and ``__view__``, registers a DynamicTable.

    Arguments:
        base: A declarative base object
        target_lag: How stale the dynamic table's content can be (e.g. ``'1 minute'``)
        warehouse: The warehouse used to refresh the dynamic table
    """
    metadata = getattr(base, "metadata", None)
    if metadata is None:
        raise ValueError("Model must have a 'metadata' attribute.")

    def decorator(cls: T) -> T:
        instance = DeclarativeDynamicTable(cls, target_lag=target_lag, warehouse=warehouse)
        register_dynamic_table(base, instance)
        return cls

    return decorator


def register_dynamic_table(
    base_or_metadata: HasMetaData | MetaData,
    dt: DynamicTable | DeclarativeDynamicTable,
):
    """Register a dynamic table onto the given declarative base or MetaData."""
    if isinstance(base_or_metadata, MetaData):
        metadata = base_or_metadata
    else:
        metadata = base_or_metadata.metadata

    if not metadata.info.get("dynamic_tables"):
        metadata.info["dynamic_tables"] = DynamicTables()
    metadata.info["dynamic_tables"].append(dt)


@dataclass
class DeclarativeDynamicTable:
    cls: type
    target_lag: str
    warehouse: str

    @property
    def name(self) -> str:
        return self.cls.__tablename__

    @property
    def table_args(self):
        return getattr(self.cls, "__table_args__", None)

    @property
    def view_def(self) -> str | Select:
        if inspect.isfunction(self.cls.__view__):
            return self.cls.__view__()
        return self.cls.__view__

    @property
    def schema(self) -> str | None:
        table_args = self.table_args
        if isinstance(table_args, dict):
            return table_args.get("schema")
        if isinstance(table_args, Iterable):
            for table_arg in table_args:
                if isinstance(table_arg, dict):
                    return table_arg.get("schema")
        return None


@dataclass
class DynamicTable:
    """Definition of a Snowflake Dynamic Table."""

    name: str
    definition: str | Select
    target_lag: str
    warehouse: str
    schema: str | None = None

    @classmethod
    def coerce_from_unknown(cls, unknown: Any) -> DynamicTable:
        if isinstance(unknown, DynamicTable):
            return cls(
                name=unknown.name.upper(),
                definition=unknown.definition,
                target_lag=unknown.target_lag,
                warehouse=unknown.warehouse.upper(),
                schema=unknown.schema.upper() if unknown.schema else None,
            )
        if isinstance(unknown, DeclarativeDynamicTable):
            return cls(
                name=unknown.name.upper(),
                definition=unknown.view_def,
                target_lag=unknown.target_lag,
                warehouse=unknown.warehouse.upper(),
                schema=unknown.schema.upper() if unknown.schema else None,
            )
        raise NotImplementedError(f"Unsupported dynamic table source: {unknown}")

    @property
    def qualified_name(self) -> str:
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

    def render_definition(self, conn: Connection) -> str:
        compiled = self.compile_definition(conn.engine.dialect)
        try:
            import sqlglot
            from sqlglot.optimizer.normalize import normalize
        except ImportError:
            raise ImportError("Dynamic table autogeneration requires the 'parse' extra.")

        return (
            escape_params(
                normalize(sqlglot.parse_one(compiled, read="snowflake")).sql("snowflake")
            )
            + ";"
        )

    def normalize(self, conn: Connection) -> Self:
        definition = self.render_definition(conn)
        return replace(
            self,
            name=self.name.upper(),
            schema=self.schema.upper() if self.schema else None,
            warehouse=self.warehouse.upper(),
            definition=definition,
        )

    def to_sql_create(self, dialect: Dialect | None = None) -> list[str]:
        definition = self.compile_definition(dialect).strip(";")
        statement = (
            f"CREATE DYNAMIC TABLE {self.qualified_name}"
            f" TARGET_LAG = '{self.target_lag}'"
            f" WAREHOUSE = {self.warehouse}"
            f" AS {definition};"
        )
        return [statement]

    def to_sql_drop(self, dialect: Dialect | None = None) -> list[str]:
        return [f"DROP DYNAMIC TABLE {self.qualified_name};"]

    def to_sql_update(
        self, from_table: DynamicTable, dialect: Dialect | None = None
    ) -> list[str]:
        result = []
        result.extend(from_table.to_sql_drop(dialect))
        result.extend(self.to_sql_create(dialect))
        return result


@dataclass
class DynamicTables:
    """Collection of Snowflake Dynamic Tables and associated comparison options."""

    dynamic_tables: list[DynamicTable | DeclarativeDynamicTable] = field(
        default_factory=list
    )
    ignore_unspecified: bool = False
    ignore: Iterable[str] = field(default_factory=set)

    @classmethod
    def coerce_from_unknown(
        cls,
        unknown: None | Iterable[DynamicTable] | DynamicTables,
    ) -> DynamicTables | None:
        if isinstance(unknown, DynamicTables):
            return unknown
        if isinstance(unknown, Iterable):
            return cls().are(*unknown)
        return None

    @classmethod
    def extract(
        cls,
        metadata: MetaData | list[MetaData] | list[MetaData | None] | None,
    ) -> Self | None:
        if not isinstance(metadata, Sequence):
            metadata = [metadata]

        instances: list[Self] = [
            m.info["dynamic_tables"]
            for m in metadata
            if m and m.info.get("dynamic_tables")
        ]

        if not instances:
            return None

        tables: list[DynamicTable | DeclarativeDynamicTable] = [
            t for instance in instances for t in instance.dynamic_tables
        ]
        ignore: list[str] = [s for instance in instances for s in instance.ignore]
        ignore_unspecified = instances[0].ignore_unspecified

        return cls(
            dynamic_tables=tables,
            ignore_unspecified=ignore_unspecified,
            ignore=ignore,
        )

    def append(self, dynamic_table: DynamicTable | DeclarativeDynamicTable):
        self.dynamic_tables.append(dynamic_table)

    def __iter__(self):
        yield from self.dynamic_tables

    def are(self, *dynamic_tables: DynamicTable) -> Self:
        return replace(self, dynamic_tables=list(dynamic_tables))


@dataclass
class CreateDynamicTableOp(ExecuteOp):
    dynamic_table: DynamicTable

    def reverse(self):
        return DropDynamicTableOp(self.dynamic_table)

    def to_sql(self, dialect: Dialect | None = None) -> list[str]:
        return self.dynamic_table.to_sql_create(dialect)


@dataclass
class UpdateDynamicTableOp(ExecuteOp):
    from_dynamic_table: DynamicTable
    dynamic_table: DynamicTable

    def reverse(self):
        return UpdateDynamicTableOp(
            from_dynamic_table=self.dynamic_table,
            dynamic_table=self.from_dynamic_table,
        )

    def to_sql(self, dialect: Dialect | None = None) -> list[str]:
        return self.dynamic_table.to_sql_update(self.from_dynamic_table, dialect)


@dataclass
class DropDynamicTableOp(ExecuteOp):
    dynamic_table: DynamicTable

    def reverse(self):
        return CreateDynamicTableOp(self.dynamic_table)

    def to_sql(self, dialect: Dialect | None = None) -> list[str]:
        return self.dynamic_table.to_sql_drop(dialect)


DynamicTableOperation = Union[CreateDynamicTableOp, UpdateDynamicTableOp, DropDynamicTableOp]


def compare_dynamic_tables(
    connection: Connection,
    dynamic_tables: DynamicTables,
) -> list[DynamicTableOperation]:
    from sqlalchemy_declarative_extensions.dialects.snowflake.query import (
        get_dynamic_tables_snowflake,
    )

    result: list[DynamicTableOperation] = []

    concrete_defined: list[DynamicTable] = [
        DynamicTable.coerce_from_unknown(dt) for dt in dynamic_tables.dynamic_tables
    ]

    by_name = {dt.qualified_name: dt for dt in concrete_defined}
    expected_names = set(by_name)

    existing = get_dynamic_tables_snowflake(connection)
    existing_by_name = {dt.qualified_name: dt for dt in existing}
    existing_names = set(existing_by_name)

    new_names = expected_names - existing_names
    removed_names = existing_names - expected_names

    for dt in concrete_defined:
        normalized = dt.normalize(connection)
        name = normalized.qualified_name

        if any(fnmatch(name, pattern) for pattern in dynamic_tables.ignore):
            continue

        if name in new_names:
            result.append(CreateDynamicTableOp(normalized))
        else:
            existing_dt = existing_by_name[name]
            normalized_existing = existing_dt.normalize(connection)

            if normalized_existing != normalized:
                result.append(UpdateDynamicTableOp(normalized_existing, normalized))

    if not dynamic_tables.ignore_unspecified:
        for removed_name in removed_names:
            if any(fnmatch(removed_name, pattern) for pattern in dynamic_tables.ignore):
                continue
            result.append(DropDynamicTableOp(existing_by_name[removed_name]))

    return result


def dynamic_table_ddl(
    dynamic_tables: DynamicTables, table_filter: list[str] | None = None
):
    def after_create(metadata: MetaData, connection: Connection, **_):
        result = compare_dynamic_tables(connection, dynamic_tables)
        for op in result:
            if not match_name(op.dynamic_table.qualified_name, table_filter):
                continue
            for command in op.to_sql(connection.dialect):
                connection.execute(text(command))

    return after_create
