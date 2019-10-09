from typing import Optional

from alembic.autogenerate.api import AutogenContext
from alembic.autogenerate.compare import comparators
from alembic.autogenerate.render import renderers
from alembic.operations import Operations

from sqlalchemy_declarative_extensions import model
from sqlalchemy_declarative_extensions.model.base import Models
from sqlalchemy_declarative_extensions.model.compare import (
    DeleteModelOp,
    InsertModelOp,
    UpdateModelOp,
)

Operations.register_operation("insert_table_row")(InsertModelOp)
Operations.register_operation("update_table_row")(UpdateModelOp)
Operations.register_operation("delete_table_row")(DeleteModelOp)


@comparators.dispatch_for("schema")
def compare_models(autogen_context: AutogenContext, upgrade_ops, _):
    if autogen_context.metadata is None:
        return

    models: Optional[Models] = autogen_context.metadata.info.get("models")
    if not models:
        return

    if autogen_context.connection is None:
        return

    result = model.compare.compare_models(
        autogen_context.connection, autogen_context.metadata, models
    )
    upgrade_ops.ops.extend(result)


@renderers.dispatch_for(InsertModelOp)
def render_insert_table_row(_, op):
    return "op.insert_table_row('{table}', {values})".format(
        table=op.table, values=op.values
    )


@renderers.dispatch_for(UpdateModelOp)
def render_update_table_row(_, op):
    return "op.update_table_row('{}', from_values={}, to_values={})".format(
        op.table, op.from_values, op.to_values
    )


@renderers.dispatch_for(DeleteModelOp)
def render_delete_table_row(_, op):
    return "op.delete_table_row('{table}', {values})".format(
        table=op.table, values=op.values
    )


@Operations.implementation_for(InsertModelOp)
def insert_model(operations: Operations, operation: InsertModelOp):
    metadata = operations.migration_context.opts["target_metadata"]
    query = operation.render(metadata)
    conn = operations.get_bind()
    conn.execute(query)


@Operations.implementation_for(UpdateModelOp)
def update_model(operations: Operations, operation: UpdateModelOp):
    metadata = operations.migration_context.opts["target_metadata"]
    query = operation.render(metadata)
    conn = operations.get_bind()
    conn.execute(query)


@Operations.implementation_for(DeleteModelOp)
def delete_model(operations: Operations, operation: DeleteModelOp):
    metadata = operations.migration_context.opts["target_metadata"]
    query = operation.render(metadata)
    conn = operations.get_bind()
    conn.execute(query)
