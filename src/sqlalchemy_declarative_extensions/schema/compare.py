from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from sqlalchemy.engine.base import Connection

from sqlalchemy_declarative_extensions.dialects import get_schemas
from sqlalchemy_declarative_extensions.role.compare import UseRoleOp
from sqlalchemy_declarative_extensions.role.state import RoleState
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

    def to_sql(self) -> list[str]:
        return [self.schema.to_sql_create()]


@dataclass
class DropSchemaOp:
    schema: Schema

    @classmethod
    def drop_schema(cls, operations, schema, **kwargs):
        op = cls(Schema(schema, **kwargs))
        return operations.invoke(op)

    def reverse(self):
        return CreateSchemaOp(self.schema)

    def to_sql(self):
        return [self.schema.to_sql_drop()]


SchemaOp = Union[CreateSchemaOp, DropSchemaOp, UseRoleOp]


def compare_schemas(connection: Connection, schemas: Schemas) -> list[SchemaOp]:
    existing_schemas = get_schemas(connection)
    role_state = RoleState.from_connection(connection)

    expected_schemas = {s.name: s for s in schemas.schemas}
    new_schemas = expected_schemas.keys() - existing_schemas.keys()
    removed_schemas = existing_schemas.keys() - expected_schemas.keys()

    result: list[SchemaOp] = []
    for schema_name in sorted(new_schemas):
        schema = expected_schemas[schema_name]

        result.extend(role_state.use_role(schema.use_role))
        result.append(CreateSchemaOp(schema))

    if not schemas.ignore_unspecified:
        for schema_name in sorted(removed_schemas, reverse=True):
            schema = existing_schemas[schema_name]

            result.extend(role_state.use_role(schema.use_role))
            result.append(DropSchemaOp(schema))

    result.extend(role_state.reset())

    return result
