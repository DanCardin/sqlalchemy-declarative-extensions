from alembic.autogenerate.api import AutogenContext
from alembic.autogenerate.compare import comparators
from alembic.autogenerate.render import renderers

from sqlalchemy_declarative_extensions.function.compare import (
    CreateFunctionOp,
    DropFunctionOp,
    UpdateFunctionOp,
    compare_functions,
)


@comparators.dispatch_for("schema")
def _compare_functions(autogen_context, upgrade_ops, _):
    metadata = autogen_context.metadata
    functions = metadata.info.get("functions")
    if not functions:
        return

    result = compare_functions(autogen_context.connection, functions, metadata)
    upgrade_ops.ops.extend(result)


@renderers.dispatch_for(CreateFunctionOp)
def render_create_function(autogen_context: AutogenContext, op: CreateFunctionOp):
    assert autogen_context.connection
    command = op.to_sql()
    return f'op.execute("""{command}""")'


@renderers.dispatch_for(UpdateFunctionOp)
def render_update_function(autogen_context: AutogenContext, op: UpdateFunctionOp):
    assert autogen_context.connection
    command = op.to_sql()
    return f'op.execute("""{command}""")'


@renderers.dispatch_for(DropFunctionOp)
def render_drop_function(autogen_context: AutogenContext, op: DropFunctionOp):
    assert autogen_context.connection
    command = op.to_sql()
    return f'op.execute("""{command}""")'
