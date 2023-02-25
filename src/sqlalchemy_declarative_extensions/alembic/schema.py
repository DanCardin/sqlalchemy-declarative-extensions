from alembic.autogenerate.compare import comparators
from alembic.autogenerate.render import renderers
from alembic.operations import Operations
from sqlalchemy.schema import CreateSchema, DropSchema

from sqlalchemy_declarative_extensions import schema
from sqlalchemy_declarative_extensions.schema.base import Schemas
from sqlalchemy_declarative_extensions.schema.compare import (
    CreateSchemaOp,
    DropSchemaOp,
)

Operations.register_operation("create_schema")(CreateSchemaOp)
Operations.register_operation("drop_schema")(DropSchemaOp)


@comparators.dispatch_for("schema")
def compare_schemas(autogen_context, upgrade_ops, schemas: Schemas):
    schemas = autogen_context.metadata.info.get("schemas")
    if not schemas:
        return

    result = schema.compare.compare_schemas(autogen_context.connection, schemas)
    upgrade_ops.ops[0:0] = result


@renderers.dispatch_for(CreateSchemaOp)
def render_create_schema(_, op: CreateSchemaOp):
    return f"op.create_schema('{op.schema.name}')"


@renderers.dispatch_for(DropSchemaOp)
def render_drop_schema(_, op: DropSchemaOp):
    return f"op.drop_schema('{op.schema.name}')"


@Operations.implementation_for(CreateSchemaOp)
def create_schema(operations, operation: CreateSchemaOp):
    operations.execute(CreateSchema(operation.schema.name))


@Operations.implementation_for(DropSchemaOp)
def drop_schema(operations, operation: DropSchemaOp):
    operations.execute(DropSchema(operation.schema.name))
