from alembic.autogenerate.api import AutogenContext
from alembic.autogenerate.compare import comparators
from alembic.autogenerate.render import renderers
from alembic.operations import Operations

from sqlalchemy_declarative_extensions.role.compare import (
    CreateRoleOp,
    DropRoleOp,
    UpdateRoleOp,
    compare_roles,
)

Operations.register_operation("create_role")(CreateRoleOp)
Operations.register_operation("update_role")(UpdateRoleOp)
Operations.register_operation("drop_role")(DropRoleOp)


@comparators.dispatch_for("schema")
def _compare_roles(autogen_context, upgrade_ops, _):
    roles = autogen_context.metadata.info.get("roles")
    if not roles:
        return

    result = compare_roles(autogen_context.connection, roles)
    upgrade_ops.ops[0:0] = result


@renderers.dispatch_for(CreateRoleOp)
def render_create_role(autogen_context: AutogenContext, op: CreateRoleOp):
    command = op.role.to_sql_create()
    return f'op.execute("""{command}""")'


@renderers.dispatch_for(UpdateRoleOp)
def render_update_role(autogen_context: AutogenContext, op: UpdateRoleOp):
    commands = op.from_role.to_sql_update(op.to_role)
    return [f'op.execute("""{command}""")' for command in commands]


@renderers.dispatch_for(DropRoleOp)
def render_drop_role(autogen_context: AutogenContext, op: DropRoleOp):
    command = op.role.to_sql_drop()
    return f'op.execute("""{command}""")'


@Operations.implementation_for(CreateRoleOp)
def create_role(operations, op):
    command = op.role.to_sql_create()
    operations.execute(command)


@Operations.implementation_for(UpdateRoleOp)
def update_role(operations, op):
    commands = op.from_role.to_sql_update(op.to_role)
    for command in commands:
        operations.execute(command)


@Operations.implementation_for(DropRoleOp)
def drop_role(operations, op):
    command = op.role.to_sql_drop()
    operations.execute(command)
