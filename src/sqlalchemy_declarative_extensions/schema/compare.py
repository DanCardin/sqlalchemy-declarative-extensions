from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Union

from sqlalchemy.engine.base import Connection
from sqlalchemy.sql.base import Executable

from sqlalchemy_declarative_extensions.dialects import get_schema_cls, get_schemas
from sqlalchemy_declarative_extensions.op import MigrateOp
from sqlalchemy_declarative_extensions.role.compare import UseRoleOp
from sqlalchemy_declarative_extensions.role.state import RoleState
from sqlalchemy_declarative_extensions.schema.base import Schema, Schemas


@dataclass
class CreateSchemaOp(MigrateOp):
    schema: Schema
    use_role_ops: list[UseRoleOp] | None = None

    @classmethod
    def create_schema(cls, operations, schema, **kwargs):
        op = cls(Schema(schema, **kwargs))
        return operations.invoke(op)

    def reverse(self):
        return DropSchemaOp(self.schema)

    def to_sql(self) -> list[Executable | str]:
        role_sql = UseRoleOp.to_sql_from_use_role_ops(self.use_role_ops)
        return [*role_sql, self.schema.to_sql_create()]

    def to_diff_tuple(self) -> tuple[Any, ...]:
        return "execute", *self.to_sql()


@dataclass
class DropSchemaOp(MigrateOp):
    schema: Schema
    role_ops: list[UseRoleOp] | None = None

    @classmethod
    def drop_schema(cls, operations, schema, **kwargs):
        op = cls(Schema(schema, **kwargs))
        return operations.invoke(op)

    def reverse(self):
        return CreateSchemaOp(self.schema)

    def to_sql(self) -> list[Executable | str]:
        role_sql = UseRoleOp.to_sql_from_use_role_ops(self.role_ops)
        return [*role_sql, self.schema.to_sql_drop()]

    def to_diff_tuple(self) -> tuple[Any, ...]:
        return "execute", *self.to_sql()


SchemaOp = Union[CreateSchemaOp, DropSchemaOp, UseRoleOp]


def compare_schemas(connection: Connection, schemas: Schemas) -> list[SchemaOp]:
    existing_schemas = get_schemas(connection)
    role_state = RoleState.from_connection(connection)

    schema_cls: type[Schema] = get_schema_cls(connection)
    expected_schemas = {}
    for schema in schemas.schemas:
        normalized_schema = schema_cls.coerce_from_unknown(schema)
        expected_schemas[normalized_schema.name] = normalized_schema

    new_schemas = expected_schemas.keys() - existing_schemas.keys()
    removed_schemas = existing_schemas.keys() - expected_schemas.keys()

    result: list[SchemaOp] = []
    for schema_name in sorted(new_schemas):
        schema = expected_schemas[schema_name]
        result.append(CreateSchemaOp(schema, role_state.use_role(schema.use_role)))

    if not schemas.ignore_unspecified:
        for schema_name in sorted(removed_schemas, reverse=True):
            schema = existing_schemas[schema_name]
            result.append(DropSchemaOp(schema, role_state.use_role(schema.use_role)))

    result.extend(role_state.reset())

    return result
