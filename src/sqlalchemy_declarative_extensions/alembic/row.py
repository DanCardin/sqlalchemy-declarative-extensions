from __future__ import annotations

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

    rows: Rows | None = autogen_context.metadata.info.get("rows")
    if not rows:
        return

    result = row.compare.compare_rows(
        autogen_context.connection, autogen_context.metadata, rows
    )
    upgrade_ops.ops.extend(result)  # type: ignore


@renderers.dispatch_for(InsertRowOp)
@renderers.dispatch_for(UpdateRowOp)
@renderers.dispatch_for(DeleteRowOp)
def render_insert_table_row(
    autogen_context: AutogenContext, op: InsertRowOp | UpdateRowOp | DeleteRowOp
):
    metadata = autogen_context.metadata
    conn = autogen_context.connection
    assert metadata
    assert conn

    result = []
    for query in op.render(metadata):
        query_str = query.compile(
            dialect=conn.dialect,
            compile_kwargs={"literal_binds": True},
        )
        result.append(f'op.execute("""{query_str}""")')
    return result


@Operations.implementation_for(InsertRowOp)
@Operations.implementation_for(UpdateRowOp)
@Operations.implementation_for(DeleteRowOp)
def execute_row(
    operations: Operations,
    operation: InsertRowOp | UpdateRowOp | DeleteRowOp,
):
    conn = operations.get_bind()
    operation.execute(conn)
