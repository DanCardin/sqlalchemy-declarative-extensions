from __future__ import annotations

from alembic.autogenerate.api import AutogenContext
from alembic.autogenerate.compare import comparators
from alembic.autogenerate.render import renderers

from sqlalchemy_declarative_extensions.procedure.base import Procedures
from sqlalchemy_declarative_extensions.procedure.compare import (
    CreateProcedureOp,
    DropProcedureOp,
    Operation,
    UpdateProcedureOp,
    compare_procedures,
)


@comparators.dispatch_for("schema")
def _compare_procedures(autogen_context: AutogenContext, upgrade_ops, _):
    procedures: Procedures | None = Procedures.extract(autogen_context.metadata)
    if not procedures:
        return

    assert autogen_context.connection
    result = compare_procedures(autogen_context.connection, procedures)
    upgrade_ops.ops.extend(result)


@renderers.dispatch_for(CreateProcedureOp)
@renderers.dispatch_for(UpdateProcedureOp)
@renderers.dispatch_for(DropProcedureOp)
def render_create_procedure(autogen_context: AutogenContext, op: Operation):
    assert autogen_context.connection
    commands = op.to_sql()
    return [f'op.execute("""{command}""")' for command in commands]
