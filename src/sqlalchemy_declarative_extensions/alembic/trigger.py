from alembic.autogenerate.api import AutogenContext
from alembic.autogenerate.compare import comparators
from alembic.autogenerate.render import renderers

from sqlalchemy_declarative_extensions.trigger.compare import (
    CreateTriggerOp,
    DropTriggerOp,
    UpdateTriggerOp,
    compare_triggers,
)


@comparators.dispatch_for("schema")
def _compare_triggers(autogen_context, upgrade_ops, _):
    metadata = autogen_context.metadata
    triggers = metadata.info.get("triggers")
    if not triggers:
        return

    result = compare_triggers(autogen_context.connection, triggers, metadata)
    upgrade_ops.ops.extend(result)


@renderers.dispatch_for(CreateTriggerOp)
def render_create_trigger(autogen_context: AutogenContext, op: CreateTriggerOp):
    assert autogen_context.connection
    commands = op.to_sql(autogen_context.connection)

    return [f'op.execute("""{command}""")' for command in commands]


@renderers.dispatch_for(UpdateTriggerOp)
def render_update_trigger(autogen_context: AutogenContext, op: UpdateTriggerOp):
    assert autogen_context.connection
    commands = op.to_sql(autogen_context.connection)

    return [f'op.execute("""{command}""")' for command in commands]


@renderers.dispatch_for(DropTriggerOp)
def render_drop_trigger(autogen_context: AutogenContext, op: DropTriggerOp):
    assert autogen_context.connection
    commands = op.to_sql(autogen_context.connection)

    return [f'op.execute("""{command}""")' for command in commands]
