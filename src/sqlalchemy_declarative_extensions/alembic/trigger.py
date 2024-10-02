from __future__ import annotations

from alembic.autogenerate.api import AutogenContext

from sqlalchemy_declarative_extensions.alembic.base import (
    register_comparator_dispatcher,
    register_renderer_dispatcher,
    register_rewriter_dispatcher,
)
from sqlalchemy_declarative_extensions.trigger.base import Triggers
from sqlalchemy_declarative_extensions.trigger.compare import (
    CreateTriggerOp,
    DropTriggerOp,
    Operation,
    UpdateTriggerOp,
    compare_triggers,
)


def _compare_triggers(autogen_context: AutogenContext, upgrade_ops, _):
    triggers: Triggers | None = Triggers.extract(autogen_context.metadata)
    if not triggers:
        return

    assert autogen_context.connection
    result = compare_triggers(autogen_context.connection, triggers)
    upgrade_ops.ops.extend(result)


def render_trigger(autogen_context: AutogenContext, op: Operation):
    assert autogen_context.connection
    commands = op.to_sql(autogen_context.connection)

    return [f'op.execute("""{command}""")' for command in commands]


register_comparator_dispatcher(_compare_triggers, target="schema")
register_renderer_dispatcher(
    CreateTriggerOp, UpdateTriggerOp, DropTriggerOp, fn=render_trigger
)
register_rewriter_dispatcher(CreateTriggerOp, UpdateTriggerOp, DropTriggerOp)
