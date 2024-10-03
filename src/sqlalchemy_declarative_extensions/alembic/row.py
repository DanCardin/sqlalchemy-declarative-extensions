from __future__ import annotations

from alembic.autogenerate.api import AutogenContext
from alembic.operations import Operations
from alembic.operations.ops import UpgradeOps
from sqlalchemy import MetaData

from sqlalchemy_declarative_extensions import row
from sqlalchemy_declarative_extensions.alembic.base import (
    register_comparator_dispatcher,
    register_operation_dispatcher,
    register_renderer_dispatcher,
    register_rewriter_dispatcher,
)
from sqlalchemy_declarative_extensions.row.base import Rows
from sqlalchemy_declarative_extensions.row.compare import (
    DeleteRowOp,
    InsertRowOp,
    UpdateRowOp,
)


def compare_rows(autogen_context: AutogenContext, upgrade_ops: UpgradeOps, _):
    optional_rows: tuple[Rows, MetaData] | None = Rows.extract(autogen_context.metadata)
    if not optional_rows:
        return

    rows, metadata = optional_rows

    assert autogen_context.connection
    result = row.compare.compare_rows(autogen_context.connection, metadata, rows)
    upgrade_ops.ops.extend(result)  # type: ignore


def render_row(
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


def execute_row(
    operations: Operations,
    operation: InsertRowOp | UpdateRowOp | DeleteRowOp,
):
    conn = operations.get_bind()
    operation.execute(conn)


register_comparator_dispatcher(compare_rows, target="schema")
register_renderer_dispatcher(InsertRowOp, UpdateRowOp, DeleteRowOp, fn=render_row)
register_rewriter_dispatcher(InsertRowOp, UpdateRowOp, DeleteRowOp)
register_operation_dispatcher(
    insert_table_row=InsertRowOp,
    update_table_row=UpdateRowOp,
    delete_table_row=DeleteRowOp,
    fn=execute_row,
)
