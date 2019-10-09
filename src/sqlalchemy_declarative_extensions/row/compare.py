from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Union

from sqlalchemy import MetaData, Table, tuple_
from sqlalchemy.engine.base import Connection

from sqlalchemy_declarative_extensions.row.base import Row, Rows


@dataclass
class InsertRowOp:
    table: str
    values: dict[str, Any]

    @classmethod
    def insert_table_row(cls, operations, table, values):
        op = cls(table, values)
        return operations.invoke(op)

    def render(self, metadata: MetaData):
        table = metadata.tables[self.table]
        return table.insert().values(self.values)

    def reverse(self):
        return DeleteRowOp(self.table, self.values)


@dataclass
class UpdateRowOp:
    table: str
    from_values: dict[str, Any]
    to_values: dict[str, Any]

    @classmethod
    def update_table_row(cls, operations, table, from_values, to_values):
        op = cls(table, from_values, to_values)
        return operations.invoke(op)

    def render(self, metadata: MetaData):
        table = metadata.tables[self.table]
        primary_key_columns = [c.name for c in table.primary_key.columns]
        where = [
            table.c[c] == v
            for c, v in self.to_values.items()
            if c in primary_key_columns
        ]
        values = {
            c: v for c, v in self.to_values.items() if c not in primary_key_columns
        }
        return table.update().where(*where).values(**values)

    def reverse(self):
        return UpdateRowOp(self.table, self.to_values, self.from_values)


@dataclass
class DeleteRowOp:
    table: str
    values: dict[str, Any]

    @classmethod
    def delete_table_row(cls, operations, table, values):
        op = cls(table, values)
        return operations.invoke(op)

    def render(self, metadata: MetaData):
        table = metadata.tables[self.table]
        primary_key_columns = [c.name for c in table.primary_key.columns]
        where = [
            table.c[c] == v for c, v in self.values.items() if c in primary_key_columns
        ]
        return table.delete().where(*where)

    def reverse(self):
        return InsertRowOp(self.table, self.values)


RowOp = Union[InsertRowOp, UpdateRowOp, DeleteRowOp]


def compare_rows(connection: Connection, metadata: MetaData, rows: Rows) -> List[RowOp]:
    result: List[RowOp] = []

    rows_by_table: Dict[Table, List[Row]] = {}
    for row in rows:
        table = metadata.tables[row.qualified_name]
        rows_by_table.setdefault(table, []).append(row)

        primary_key_columns = [c.name for c in table.primary_key.columns]

        if set(primary_key_columns) - row.column_values.keys():
            raise ValueError(
                f"Row is missing primary key values required to declaratively specify: {row}"
            )

        column_filters = [
            c == row.column_values[c.name] for c in table.primary_key.columns
        ]
        record = connection.execute(
            table.select().where(*column_filters).limit(1)
        ).first()
        if record:
            row_keys = row.column_values.keys()
            record_dict = {k: v for k, v in dict(record).items() if k in row_keys}
            if row.column_values == record_dict:
                continue
            else:
                result.append(
                    UpdateRowOp(
                        row.qualified_name,
                        from_values=record_dict,
                        to_values=row.column_values,
                    )
                )
        else:
            result.append(InsertRowOp(row.qualified_name, values=row.column_values))

    if not rows.ignore_unspecified:
        for table_name in rows.included_tables:
            table = metadata.tables[table_name]
            rows_by_table.setdefault(table, [])

        for table, row_list in rows_by_table.items():
            primary_key_columns = [c.name for c in table.primary_key.columns]
            primary_key_values = [
                tuple(row.column_values[c] for c in primary_key_columns)
                for row in row_list
            ]
            to_delete = connection.execute(
                table.select().where(
                    tuple_(*table.primary_key.columns).notin_(primary_key_values)
                )
            ).all()

            for record in to_delete:
                op = DeleteRowOp(table.name, dict(record))
                result.append(op)

    return result
