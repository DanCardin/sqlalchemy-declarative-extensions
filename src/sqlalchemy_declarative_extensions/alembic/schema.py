from __future__ import annotations

from alembic.autogenerate.api import AutogenContext
from alembic.autogenerate.compare import comparators
from alembic.autogenerate.render import renderers
from alembic.operations import Operations

from sqlalchemy_declarative_extensions import schema
from sqlalchemy_declarative_extensions.schema.base import Schemas
from sqlalchemy_declarative_extensions.schema.compare import (
    CreateSchemaOp,
    DropSchemaOp,
)

Operations.register_operation("create_schema")(CreateSchemaOp)
Operations.register_operation("drop_schema")(DropSchemaOp)


@comparators.dispatch_for("schema")
def compare_schemas(autogen_context: AutogenContext, upgrade_ops, _):
    assert autogen_context.metadata
    schemas: Schemas | None = autogen_context.metadata.info.get("schemas")
    if not schemas:
        return

    assert autogen_context.connection
    result = schema.compare.compare_schemas(autogen_context.connection, schemas)
    upgrade_ops.ops[0:0] = result


@renderers.dispatch_for(CreateSchemaOp)
@renderers.dispatch_for(DropSchemaOp)
def render_create_schema(autogen_context: AutogenContext, op: CreateSchemaOp):
    statement = op.to_sql()
    cls_name = statement.__class__.__name__
    autogen_context.imports.add(f"from sqlalchemy.sql.ddl import {cls_name}")
    return f'op.execute({cls_name}("{statement.element}"))'


@Operations.implementation_for(CreateSchemaOp)
@Operations.implementation_for(DropSchemaOp)
def create_schema(operations, operation: CreateSchemaOp):
    operations.execute(operation.to_sql())
