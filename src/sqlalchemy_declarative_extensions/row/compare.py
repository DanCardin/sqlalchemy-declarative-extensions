from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Union

from sqlalchemy.engine.base import Connection
from sqlalchemy.sql.expression import and_, not_, null, or_, text
from sqlalchemy.sql.schema import MetaData, Table

from sqlalchemy_declarative_extensions.dialects import (
    check_table_exists,
)
from sqlalchemy_declarative_extensions.row.base import Row, Rows
from sqlalchemy_declarative_extensions.sql import split_schema
from sqlalchemy_declarative_extensions.sqlalchemy import row_to_dict, select


@dataclass
class InsertRowOp:
    table: str
    values: dict[str, Any] | list[dict[str, Any]]

    @classmethod
    def insert_table_row(cls, operations, table, values):
        op = cls(table, values)
        return operations.invoke(op)

    def render(self, metadata: MetaData):
        assert metadata.tables is not None
        table = metadata.tables[self.table]
        return [table.insert().values(self.values)]

    def execute(self, conn: Connection):
        metadata = get_metadata(conn, self.table)

        for query in self.render(metadata):
            conn.execute(query)

    def reverse(self):
        return DeleteRowOp(self.table, self.values)


@dataclass
class UpdateRowOp:
    table: str
    from_values: dict[str, Any] | list[dict[str, Any]]
    to_values: dict[str, Any] | list[dict[str, Any]]

    @classmethod
    def update_table_row(cls, operations, table, from_values, to_values):
        op = cls(table, from_values, to_values)
        return operations.invoke(op)

    def render(self, metadata: MetaData):
        assert metadata.tables is not None
        table = metadata.tables[self.table]

        primary_key_columns = [c.name for c in table.primary_key.columns]

        if isinstance(self.to_values, dict):
            to_values: list[dict[str, Any]] = [self.to_values]
        else:
            to_values = self.to_values

        result = []
        for to_value in to_values:
            where = [
                table.c[c] == v for c, v in to_value.items() if c in primary_key_columns
            ]
            values = {c: v for c, v in to_value.items() if c not in primary_key_columns}
            query = table.update().where(*where).values(**values)
            result.append(query)
        return result

    def execute(self, conn: Connection):
        metadata = get_metadata(conn, self.table)

        for query in self.render(metadata):
            conn.execute(query)

    def reverse(self):
        return UpdateRowOp(self.table, self.to_values, self.from_values)


@dataclass
class DeleteRowOp:
    table: str
    values: dict[str, Any] | list[dict[str, Any]]

    @classmethod
    def delete_table_row(cls, operations, table, values):
        op = cls(table, values)
        return operations.invoke(op)

    def render(self, metadata: MetaData):
        assert metadata.tables is not None
        table = metadata.tables[self.table]

        if isinstance(self.values, dict):
            rows_values: list[dict[str, Any]] = [self.values]
        else:
            rows_values = self.values

        primary_key_columns = {c.name for c in table.primary_key.columns}

        where = or_(
            *[
                and_(
                    *[
                        table.c[c] == v
                        for c, v in row_values.items()
                        if c in primary_key_columns
                    ]
                )
                for row_values in rows_values
            ]
        )
        return [table.delete().where(where)]

    def execute(self, conn: Connection):
        metadata = get_metadata(conn, self.table)

        for query in self.render(metadata):
            conn.execute(query)

    def reverse(self):
        return InsertRowOp(self.table, self.values)


def get_metadata(conn: Connection, tablename: str):
    m = MetaData()

    try:
        schema, table = tablename.split(".", 1)
    except ValueError:
        table = tablename
        schema = None

    m.reflect(conn, schema=schema, only=[table])
    return m


RowOp = Union[InsertRowOp, UpdateRowOp, DeleteRowOp]


def compare_rows(connection: Connection, metadata: MetaData, rows: Rows) -> list[RowOp]:
    assert metadata.tables is not None

    result: list[RowOp] = []

    existing_tables = resolve_existing_tables(connection, rows)

    # Collects table-specific primary keys so that we can efficiently compare rows
    # further down by the pk
    pk_to_row: dict[str, dict[tuple[Any, ...], Row]] = {}

    # Collects the ongoing filter required to select all referenced records (by their pk)
    filters_by_table: dict[Table, list] = {}
    for row in rows:
        table = metadata.tables.get(row.qualified_name)
        if table is None:
            raise ValueError(f"Unknown table: {row.qualified_name}")

        primary_key_columns = [c.name for c in table.primary_key.columns]

        if set(primary_key_columns) - row.column_values.keys():
            raise ValueError(
                f"Row is missing primary key values required to declaratively specify: {row}"
            )

        table = metadata.tables.get(row.qualified_name)
        if table is None:
            continue

        pk = tuple([row.column_values[c.name] for c in table.primary_key.columns])
        pk_to_row.setdefault(table.fullname, {})[pk] = row

        if table.primary_key.columns:
            filters_by_table.setdefault(table, []).append(
                and_(
                    *[c == row.column_values[c.name] for c in table.primary_key.columns]
                )
            )

    existing_rows_by_table = collect_existing_record_data(
        connection, filters_by_table, existing_tables
    )

    existing_metadata = MetaData()
    assert existing_metadata.tables is not None

    table_row_inserts: dict[Table, list[dict[str, Any]]] = {}
    table_row_updates: dict[
        Table, tuple[list[dict[str, Any]], list[dict[str, Any]]]
    ] = {}
    for tablename, pks in pk_to_row.items():
        dest_table = metadata.tables[tablename]

        row_inserts = table_row_inserts.setdefault(dest_table, [])

        existing_rows = existing_rows_by_table.get(tablename, {})

        stub_keys = {
            key: None for row in pks.values() for key in row.column_values.keys()
        }

        for pk, row in pks.items():
            if pk in existing_rows:
                if row.qualified_name not in existing_metadata.tables:
                    existing_metadata.reflect(
                        bind=connection, schema=row.schema, only=[row.tablename]
                    )
                current_table: Table = existing_metadata.tables[tablename]

                existing_row = existing_rows[pk]
                row_keys = row.column_values.keys()
                record_dict = {k: v for k, v in existing_row.items() if k in row_keys}

                column_values = filter_column_data(current_table, row.column_values)
                if column_values == record_dict:
                    continue

                row_updates = table_row_updates.setdefault(current_table, ([], []))
                row_updates[0].append(record_dict)
                row_updates[1].append(column_values)
            else:
                insert_values = {**stub_keys, **row.column_values}
                row_inserts.append(filter_column_data(dest_table, insert_values))

    # Deletes should get inserted first, so as to avoid foreign key constraint errors.
    if not rows.ignore_unspecified:
        for table_name in rows.included_tables:
            table = metadata.tables[table_name]
            filters_by_table.setdefault(table, [])

        for table, filter in filters_by_table.items():
            table_exists = existing_tables[table.fullname]
            if not table_exists:
                continue

            statement = select(*table.primary_key)
            if filter:
                statement = statement.where(not_(or_(*filter)))

            to_delete = connection.execute(statement).fetchall()

            if not to_delete:
                continue

            result.append(
                DeleteRowOp(
                    table.fullname, [row_to_dict(record) for record in to_delete]
                )
            )

    for table, row_updates in table_row_updates.items():
        old_rows, new_rows = row_updates
        if not new_rows:
            continue

        result.append(
            UpdateRowOp(
                table.fullname,
                from_values=old_rows,
                to_values=new_rows,
            )
        )

    for table, row_inserts in table_row_inserts.items():
        if not row_inserts:
            continue

        result.append(InsertRowOp(table.fullname, values=row_inserts))

    return result


def resolve_existing_tables(connection: Connection, rows: Rows) -> dict[str, bool]:
    """Collect a map of referenced tables, to whether or not they exist."""
    result = {}
    for row in rows:
        if row.qualified_name in result:
            continue

        table_exists = check_table_exists(
            connection,
            row.tablename,
            schema=row.schema,
        )
        result[row.qualified_name] = table_exists

    for fq_tablename in rows.included_tables:
        schema, tablename = split_schema(fq_tablename)
        result[fq_tablename] = check_table_exists(
            connection,
            tablename,
            schema=schema,
        )

    return result


def collect_existing_record_data(
    connection: Connection,
    filters_by_table,
    existing_tables: dict[str, bool],
) -> dict[str, dict[tuple[Any, ...], dict[str, Any]]]:
    result: dict[str, dict[tuple[Any, ...], dict[str, Any]]] = {}
    for table, filters in filters_by_table.items():
        table_exists = existing_tables[table.fullname]
        if not table_exists:
            result[table.fullname] = {}
            continue

        primary_key_columns = [c.name for c in table.primary_key.columns]

        query = select(text("*")).select_from(table).where(or_(*filters))
        records = connection.execute(query)
        assert records

        existing_rows = result.setdefault(table.fullname, {})
        for record in records.fetchall():
            record_dict = row_to_dict(record)
            pk = tuple([record_dict[c] for c in primary_key_columns])
            existing_rows[pk] = record_dict

    return result


def filter_column_data(table: Table, row: dict):
    return {
        c: v if v is not None else null() for c, v in row.items() if c in table.columns
    }
