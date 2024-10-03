from __future__ import annotations

from alembic.autogenerate.api import AutogenContext

from sqlalchemy_declarative_extensions.alembic.base import (
    register_comparator_dispatcher,
    register_renderer_dispatcher,
    register_rewriter_dispatcher,
)
from sqlalchemy_declarative_extensions.view.base import Views
from sqlalchemy_declarative_extensions.view.compare import (
    CreateViewOp,
    DropViewOp,
    Operation,
    UpdateViewOp,
    compare_views,
)


def _compare_views(autogen_context: AutogenContext, upgrade_ops, _):
    views: Views | None = Views.extract(autogen_context.metadata)
    if not views:
        return

    assert autogen_context.connection
    result = compare_views(autogen_context.connection, views)
    upgrade_ops.ops.extend(result)


def render_view(autogen_context: AutogenContext, op: Operation):
    assert autogen_context.connection
    dialect = autogen_context.connection.dialect
    commands = op.to_sql(dialect)

    return [f'op.execute("""{command}""")' for command in commands]


register_comparator_dispatcher(_compare_views, target="schema")
register_renderer_dispatcher(CreateViewOp, UpdateViewOp, DropViewOp, fn=render_view)
register_rewriter_dispatcher(CreateViewOp, UpdateViewOp, DropViewOp)
