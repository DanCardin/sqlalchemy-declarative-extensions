from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Union

from sqlalchemy import MetaData, Table, and_, not_, or_
from sqlalchemy.engine.base import Connection

from sqlalchemy_declarative_extensions.dialects import (
    check_table_exists,
    get_current_schema,
)
from sqlalchemy_declarative_extensions.row.base import Row, Rows
from sqlalchemy_declarative_extensions.sql import split_schema
from sqlalchemy_declarative_extensions.sqlalchemy import row_to_dict


@dataclass
class InsertRowOp:
    table: str
    values: dict[str, Any] | list[dict[str, Any]]

    @classmethod
    def insert_table_row(cls, operations, table, values):
        op = cls(table, values)
        return operations.invoke(op)

    def execute(self, conn: Connection):
        table = get_table(conn, self.table)
        query = table.insert().values(self.values)
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

    def execute(self, conn: Connection):
        table = get_table(conn, self.table)

        primary_key_columns = [c.name for c in table.primary_key.columns]

        if isinstance(self.to_values, dict):
            to_values: list[dict[str, Any]] = [self.to_values]
        else:
            to_values = self.to_values

        for to_value in to_values:
            where = [
                table.c[c] == v for c, v in to_value.items() if c in primary_key_columns
            ]
            values = {c: v for c, v in to_value.items() if c not in primary_key_columns}
            query = table.update().where(*where).values(**values)
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

    def execute(self, conn: Connection):
        table = get_table(conn, self.table)

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
        query = table.delete().where(where)
        conn.execute(query)

    def reverse(self):
        return InsertRowOp(self.table, self.values)


def get_table(conn: Connection, tablename: str):
    m = MetaData()

    try:
        schema, table = tablename.split(".", 1)
    except ValueError:
        table = tablename
        schema = None

    m.reflect(conn, schema=schema, only=[table])
    return m.tables[tablename]


RowOp = Union[InsertRowOp, UpdateRowOp, DeleteRowOp]


def compare_rows(connection: Connection, metadata: MetaData, rows: Rows) -> list[RowOp]:
    result: list[RowOp] = []

    current_schema = get_current_schema(connection)

    existing_tables = resolve_existing_tables(connection, rows, current_schema)

    # Collects table-specific primary keys so that we can efficiently compare rows
    # further down by the pk
    pk_to_row: dict[Table, dict[tuple[Any, ...], Row]] = {}

    # Collects the ongoing filter required to select all referenced records (by their pk)
    filters_by_table: dict[Table, list] = {}
    for row in rows:
        row = row.qualify(current_schema)

        table = metadata.tables.get(row.qualified_name)
        if table is None:
            raise ValueError(f"Unknown table: {row.qualified_name}")

        primary_key_columns = [c.name for c in table.primary_key.columns]

        if set(primary_key_columns) - row.column_values.keys():
            raise ValueError(
                f"Row is missing primary key values required to declaratively specify: {row}"
            )

        pk = tuple([row.column_values[c.name] for c in table.primary_key.columns])
        pk_to_row.setdefault(table, {})[pk] = row
        filters_by_table.setdefault(table, []).append(
            and_(*[c == row.column_values[c.name] for c in table.primary_key.columns])
        )

    existing_rows_by_table = collect_existing_record_data(
        connection, filters_by_table, existing_tables
    )

    table_row_inserts: dict[Table, list[dict[str, Any]]] = {}
    table_row_updates: dict[
        Table, tuple[list[dict[str, Any]], list[dict[str, Any]]]
    ] = {}
    for table, pks in pk_to_row.items():
        row_inserts = table_row_inserts.setdefault(table, [])
        row_updates = table_row_updates.setdefault(table, ([], []))

        existing_rows = existing_rows_by_table[table]

        stub_keys = {
            key: None for row in pks.values() for key in row.column_values.keys()
        }

        for pk, row in pks.items():
            if pk in existing_rows:
                existing_row = existing_rows[pk]
                row_keys = row.column_values.keys()
                record_dict = {k: v for k, v in existing_row.items() if k in row_keys}
                if row.column_values == record_dict:
                    continue

                row_updates[0].append(record_dict)
                row_updates[1].append(row.column_values)
            else:
                row_inserts.append({**stub_keys, **row.column_values})

    # Deletes should get inserted first, so as to avoid foreign key constraint errors.
    if not rows.ignore_unspecified:
        for table_name in rows.included_tables:
            table = metadata.tables[table_name]
            filters_by_table.setdefault(table, [])

        for table, filter in filters_by_table.items():
            table_exists = existing_tables[table.fullname]
            if not table_exists:
                continue

            select = table.select()
            if filter:
                select = select.where(not_(or_(*filter)))

            to_delete = connection.execute(select).fetchall()

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


def resolve_existing_tables(
    connection: Connection, rows: Rows, current_schema: str | None = None
) -> dict[str, bool]:
    """Collect a map of referenced tables, to whether or not they exist."""
    result = {}
    for row in rows:
        row = row.qualify(current_schema)
        if row.qualified_name in result:
            continue

        # If the table doesn't exist yet, we can likely assume it's being autogenerated
        # in the current revision and as such, will just emit insert statements.
        result[row.qualified_name] = check_table_exists(
            connection,
            row.tablename,
            schema=row.schema,
        )

    for fq_tablename in rows.included_tables:
        schema, tablename = split_schema(fq_tablename)
        result[fq_tablename] = check_table_exists(
            connection,
            tablename,
            schema=schema,
        )

    return result


def collect_existing_record_data(
    connection: Connection, filters_by_table, existing_tables: dict[str, bool]
) -> dict[Table, dict[tuple[Any, ...], dict[str, Any]]]:
    result = {}
    for table, filters in filters_by_table.items():
        table_exists = existing_tables[table.fullname]
        if not table_exists:
            result[table] = {}
            continue

        primary_key_columns = [c.name for c in table.primary_key.columns]

        records = connection.execute(table.select().where(or_(*filters))).fetchall()
        existing_rows = result.setdefault(table, {})
        for record in records:
            record_dict = row_to_dict(record)
            pk = tuple([record_dict[c] for c in primary_key_columns])
            existing_rows[pk] = record_dict
    return result
