from __future__ import annotations

from alembic.autogenerate.api import AutogenContext
from sqlalchemy.sql.ddl import CreateSchema, DropSchema

from sqlalchemy_declarative_extensions import schema
from sqlalchemy_declarative_extensions.alembic.base import (
    register_comparator_dispatcher,
    register_operation_dispatcher,
    register_renderer_dispatcher,
    register_rewriter_dispatcher,
)
from sqlalchemy_declarative_extensions.schema.base import Schemas
from sqlalchemy_declarative_extensions.schema.compare import (
    CreateSchemaOp,
    DropSchemaOp,
    SchemaOp,
)


def compare_schemas(autogen_context: AutogenContext, upgrade_ops, _):
    schemas: Schemas | None = Schemas.extract(autogen_context.metadata)
    if not schemas:
        return

    assert autogen_context.connection
    result = schema.compare.compare_schemas(autogen_context.connection, schemas)
    upgrade_ops.ops[0:0] = result


def render_schema(autogen_context: AutogenContext, op: SchemaOp):
    statements = op.to_sql()
    cls_names = {
        s.__class__.__name__
        for s in statements
        if isinstance(s, (CreateSchema, DropSchema))
    }

    if cls_names:
        autogen_context.imports.add(
            f"from sqlalchemy.sql.ddl import {', '.join(cls_names)}"
        )

    return [
        f'op.execute({command.__class__.__name__}("{command.element}"))'
        if isinstance(command, (CreateSchema, DropSchema))
        else f'op.execute("""{command}""")'
        for command in statements
    ]


def schema_operation(operations, operation: SchemaOp):
    for command in operation.to_sql():
        operations.execute(command)


register_comparator_dispatcher(compare_schemas, "schema")
register_renderer_dispatcher(CreateSchemaOp, DropSchemaOp, fn=render_schema)
register_rewriter_dispatcher(CreateSchemaOp, DropSchemaOp)
register_operation_dispatcher(
    create_schema=CreateSchemaOp, drop_schema=DropSchemaOp, fn=schema_operation
)
