from alembic.autogenerate.api import AutogenContext
from alembic.autogenerate.compare import comparators
from alembic.autogenerate.render import renderers

from sqlalchemy_declarative_extensions.procedure.compare import (
    CreateProcedureOp,
    DropProcedureOp,
    Operation,
    UpdateProcedureOp,
    compare_procedures,
)


@comparators.dispatch_for("schema")
def _compare_procedures(autogen_context, upgrade_ops, _):
    metadata = autogen_context.metadata
    procedures = metadata.info.get("procedures")
    if not procedures:
        return

    result = compare_procedures(autogen_context.connection, procedures, metadata)
    upgrade_ops.ops.extend(result)


@renderers.dispatch_for(CreateProcedureOp)
@renderers.dispatch_for(UpdateProcedureOp)
@renderers.dispatch_for(DropProcedureOp)
def render_create_procedure(autogen_context: AutogenContext, op: Operation):
    assert autogen_context.connection
    command = op.to_sql()
    return f'op.execute("""{command}""")'
