from __future__ import annotations

from dataclasses import dataclass
from typing import List, Union

from sqlalchemy.engine.base import Connection
from sqlalchemy.sql.expression import text

from sqlalchemy_declarative_extensions.schema.base import Schema, Schemas
from sqlalchemy_declarative_extensions.sqlalchemy import dialect_dispatch


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


def compare_schemas(connection: Connection, schemas: Schemas) -> List[SchemaOp]:
    existing_schemas = get_existing_schemas(connection)

    expected_schemas = set(schemas.schemas)
    new_schemas = expected_schemas - existing_schemas
    removed_schemas = existing_schemas - expected_schemas

    result: List[SchemaOp] = []
    for schema in sorted(new_schemas):
        result.insert(0, CreateSchemaOp(schema))

    if not schemas.ignore_unspecified:
        for schema in reversed(sorted(removed_schemas)):
            result.append(DropSchemaOp(schema))

    return result


def get_existing_schemas_postgresql(connection: Connection):
    default_schema = connection.dialect.default_schema_name
    select_schemas = text("SELECT nspname FROM pg_catalog.pg_namespace")

    return {
        Schema(schema)
        for schema, *_ in connection.execute(select_schemas).fetchall()
        if not schema.startswith("pg_")
        and schema not in {"information_schema", default_schema}
    }


get_existing_schemas = dialect_dispatch(
    postgresql=get_existing_schemas_postgresql,
)
