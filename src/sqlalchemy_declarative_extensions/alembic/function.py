from __future__ import annotations

from alembic.autogenerate.api import AutogenContext
from alembic.autogenerate.compare import comparators
from alembic.autogenerate.render import renderers

from sqlalchemy_declarative_extensions.function.base import Functions
from sqlalchemy_declarative_extensions.function.compare import (
    CreateFunctionOp,
    DropFunctionOp,
    Operation,
    UpdateFunctionOp,
    compare_functions,
)


@comparators.dispatch_for("schema")
def _compare_functions(autogen_context: AutogenContext, upgrade_ops, _):
    functions: Functions | None = Functions.extract(autogen_context.metadata)
    if not functions:
        return

    assert autogen_context.connection
    result = compare_functions(autogen_context.connection, functions)
    upgrade_ops.ops.extend(result)


@renderers.dispatch_for(CreateFunctionOp)
@renderers.dispatch_for(UpdateFunctionOp)
@renderers.dispatch_for(DropFunctionOp)
def render_create_function(autogen_context: AutogenContext, op: Operation):
    assert autogen_context.connection
    commands = op.to_sql()
    return [f'op.execute("""{command}""")' for command in commands]
