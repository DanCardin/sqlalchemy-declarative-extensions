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
@renderers.dispatch_for(DropRoleOp)
@renderers.dispatch_for(UpdateRoleOp)
def render_role(autogen_context: AutogenContext, op: CreateRoleOp):
    return [f'op.execute("""{command}""")' for command in op.to_sql()]


@Operations.implementation_for(CreateRoleOp)
@Operations.implementation_for(UpdateRoleOp)
@Operations.implementation_for(DropRoleOp)
def create_role(operations, op):
    commands = op.to_sql()
    for command in commands:
        operations.execute(command)
