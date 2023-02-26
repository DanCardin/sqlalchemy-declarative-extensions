from typing import Optional, Union

from alembic.autogenerate.api import AutogenContext
from alembic.autogenerate.compare import comparators
from alembic.autogenerate.render import renderers
from alembic.operations import Operations
from alembic.operations.ops import UpgradeOps

from sqlalchemy_declarative_extensions import row
from sqlalchemy_declarative_extensions.row.base import Rows
from sqlalchemy_declarative_extensions.row.compare import (
    DeleteRowOp,
    InsertRowOp,
    UpdateRowOp,
)

Operations.register_operation("insert_table_row")(InsertRowOp)
Operations.register_operation("update_table_row")(UpdateRowOp)
Operations.register_operation("delete_table_row")(DeleteRowOp)


@comparators.dispatch_for("schema")
def compare_rows(autogen_context: AutogenContext, upgrade_ops: UpgradeOps, _):
    if (
        autogen_context.metadata is None or autogen_context.connection is None
    ):  # pragma: no cover
        return

    rows: Optional[Rows] = autogen_context.metadata.info.get("rows")
    if not rows:
        return

    result = row.compare.compare_rows(
        autogen_context.connection, autogen_context.metadata, rows
    )
    upgrade_ops.ops.extend(result)  # type: ignore


@renderers.dispatch_for(InsertRowOp)
def render_insert_table_row(_, op: InsertRowOp):
    return "op.insert_table_row('{table}', {values})".format(
        table=op.table, values=op.values
    )


@renderers.dispatch_for(UpdateRowOp)
def render_update_table_row(_, op: UpdateRowOp):
    return "op.update_table_row('{}', from_values={}, to_values={})".format(
        op.table, op.from_values, op.to_values
    )


@renderers.dispatch_for(DeleteRowOp)
def render_delete_table_row(_, op: DeleteRowOp):
    return "op.delete_table_row('{table}', {values})".format(
        table=op.table, values=op.values
    )


@Operations.implementation_for(InsertRowOp)
@Operations.implementation_for(UpdateRowOp)
@Operations.implementation_for(DeleteRowOp)
def execute_row(
    operations: Operations,
    operation: Union[InsertRowOp, UpdateRowOp, DeleteRowOp],
):
    conn = operations.get_bind()
    query = operation.render(conn)
    conn.execute(query)
