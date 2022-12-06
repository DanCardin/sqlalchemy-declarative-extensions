from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from sqlalchemy.engine.base import Connection

from sqlalchemy_declarative_extensions.dialects import get_schemas
from sqlalchemy_declarative_extensions.schema.base import Schema, Schemas


@dataclass
class CreateSchemaOp:
    schema: Schema

    @classmethod
    def create_schema(cls, operations, schema, **kwargs):
        op = cls(Schema(schema, **kwargs))
        return operations.invoke(op)

    def reverse(self):
        return DropSchemaOp(self.schema)


@dataclass
class DropSchemaOp:
    schema: Schema

    @classmethod
    def drop_schema(cls, operations, schema, **kwargs):
        op = cls(Schema(schema, **kwargs))
        return operations.invoke(op)

    def reverse(self):
        return CreateSchemaOp(self.schema)


SchemaOp = Union[CreateSchemaOp, DropSchemaOp]


def compare_schemas(connection: Connection, schemas: Schemas) -> list[SchemaOp]:
    existing_schemas = get_schemas(connection)

    expected_schemas = set(schemas.schemas)
    new_schemas = expected_schemas - existing_schemas
    removed_schemas = existing_schemas - expected_schemas

    result: list[SchemaOp] = []
    for schema in sorted(new_schemas):
        result.insert(0, CreateSchemaOp(schema))

    if not schemas.ignore_unspecified:
        for schema in sorted(removed_schemas, reverse=True):
            result.append(DropSchemaOp(schema))

    return result
