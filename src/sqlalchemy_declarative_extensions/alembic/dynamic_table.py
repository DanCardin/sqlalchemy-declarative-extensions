from __future__ import annotations

from alembic.autogenerate.api import AutogenContext

from sqlalchemy_declarative_extensions.alembic.base import (
    register_comparator_dispatcher,
    register_renderer_dispatcher,
    register_rewriter_dispatcher,
)
from sqlalchemy_declarative_extensions.dialects.snowflake.dynamic_table import (
    CreateDynamicTableOp,
    DropDynamicTableOp,
    DynamicTableOperation,
    DynamicTables,
    UpdateDynamicTableOp,
    compare_dynamic_tables,
)


def _compare_dynamic_tables(autogen_context: AutogenContext, upgrade_ops, _):
    dynamic_tables: DynamicTables | None = DynamicTables.extract(autogen_context.metadata)
    if not dynamic_tables:
        return

    assert autogen_context.connection
    result = compare_dynamic_tables(autogen_context.connection, dynamic_tables)
    upgrade_ops.ops.extend(result)


def render_dynamic_table(autogen_context: AutogenContext, op: DynamicTableOperation):
    assert autogen_context.connection
    dialect = autogen_context.connection.dialect
    commands = op.to_sql(dialect)
    return [f'op.execute("""{command}""")' for command in commands]


register_comparator_dispatcher(_compare_dynamic_tables, target="schema")
register_renderer_dispatcher(
    CreateDynamicTableOp, UpdateDynamicTableOp, DropDynamicTableOp, fn=render_dynamic_table
)
register_rewriter_dispatcher(CreateDynamicTableOp, UpdateDynamicTableOp, DropDynamicTableOp)
