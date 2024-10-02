from __future__ import annotations

from alembic.autogenerate.api import AutogenContext

from sqlalchemy_declarative_extensions.alembic.base import (
    register_comparator_dispatcher,
    register_renderer_dispatcher,
    register_rewriter_dispatcher,
)
from sqlalchemy_declarative_extensions.procedure.base import Procedures
from sqlalchemy_declarative_extensions.procedure.compare import (
    CreateProcedureOp,
    DropProcedureOp,
    Operation,
    UpdateProcedureOp,
    compare_procedures,
)


def _compare_procedures(autogen_context: AutogenContext, upgrade_ops, _):
    procedures: Procedures | None = Procedures.extract(autogen_context.metadata)
    if not procedures:
        return

    assert autogen_context.connection
    result = compare_procedures(autogen_context.connection, procedures)
    upgrade_ops.ops.extend(result)


def render_precedure(autogen_context: AutogenContext, op: Operation):
    assert autogen_context.connection
    commands = op.to_sql()
    return [f'op.execute("""{command}""")' for command in commands]


register_comparator_dispatcher(_compare_procedures, target="schema")
register_renderer_dispatcher(
    CreateProcedureOp, UpdateProcedureOp, DropProcedureOp, fn=render_precedure
)
register_rewriter_dispatcher(CreateProcedureOp, UpdateProcedureOp, DropProcedureOp)
