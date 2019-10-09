from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Union

from sqlalchemy import MetaData, Table, tuple_
from sqlalchemy.engine.base import Connection

from sqlalchemy_declarative_extensions.model.base import Model, Models


@dataclass
class InsertModelOp:
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
        return DeleteModelOp(self.table, self.values)


@dataclass
class UpdateModelOp:
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
        return UpdateModelOp(self.table, self.to_values, self.from_values)


@dataclass
class DeleteModelOp:
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
        return InsertModelOp(self.table, self.values)


ModelOp = Union[InsertModelOp, UpdateModelOp, DeleteModelOp]


def compare_models(
    connection: Connection, metadata: MetaData, models: Models
) -> List[ModelOp]:
    result: List[ModelOp] = []

    models_by_table: Dict[Table, List[Model]] = {}
    for model in models:
        table = metadata.tables[model.qualified_name]
        models_by_table.setdefault(table, []).append(model)

        primary_key_columns = [c.name for c in table.primary_key.columns]

        if set(primary_key_columns) - model.column_values.keys():
            raise ValueError(
                f"Model is missing primary key values required to declaratively specify: {model}"
            )

        column_filters = [
            c == model.column_values[c.name] for c in table.primary_key.columns
        ]
        record = connection.execute(
            table.select().where(*column_filters).limit(1)
        ).first()
        if record:
            record_dict = dict(record)
            if model.column_values == record_dict:
                continue
            else:
                result.append(
                    UpdateModelOp(
                        model.qualified_name,
                        from_values=record_dict,
                        to_values=model.column_values,
                    )
                )
        else:
            result.append(
                InsertModelOp(model.qualified_name, values=model.column_values)
            )

    if not models.ignore_unspecified:
        for table_name in models.included_tables:
            table = metadata.tables[table_name]
            models_by_table.setdefault(table, [])

        for table, model_list in models_by_table.items():
            primary_key_columns = [c.name for c in table.primary_key.columns]
            primary_key_values = [
                tuple(model.column_values[c] for c in primary_key_columns)
                for model in model_list
            ]
            to_delete = connection.execute(
                table.select().where(
                    tuple_(*table.primary_key.columns).notin_(primary_key_values)
                )
            ).all()

            for record in to_delete:
                op = DeleteModelOp(table.name, dict(record))
                result.append(op)

    return result
