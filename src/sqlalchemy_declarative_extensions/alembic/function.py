from __future__ import annotations

from alembic.autogenerate.api import AutogenContext

from sqlalchemy_declarative_extensions.alembic.base import (
    register_comparator_dispatcher,
    register_renderer_dispatcher,
    register_rewriter_dispatcher,
)
from sqlalchemy_declarative_extensions.function.base import Functions
from sqlalchemy_declarative_extensions.function.compare import (
    CreateFunctionOp,
    DropFunctionOp,
    Operation,
    UpdateFunctionOp,
    compare_functions,
)


def _compare_functions(autogen_context: AutogenContext, upgrade_ops, _):
    functions: Functions | None = Functions.extract(autogen_context.metadata)
    if not functions:
        return

    assert autogen_context.connection
    result = compare_functions(autogen_context.connection, functions)
    upgrade_ops.ops.extend(result)


def render_create_function(autogen_context: AutogenContext, op: Operation):
    assert autogen_context.connection
    commands = op.to_sql()
    return [f'op.execute("""{command}""")' for command in commands]


register_comparator_dispatcher(_compare_functions, target="schema")
register_rewriter_dispatcher(CreateFunctionOp, UpdateFunctionOp, DropFunctionOp)
register_renderer_dispatcher(
    CreateFunctionOp, UpdateFunctionOp, DropFunctionOp, fn=render_create_function
)
