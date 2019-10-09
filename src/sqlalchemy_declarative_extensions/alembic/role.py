from alembic.autogenerate.compare import comparators
from alembic.autogenerate.render import renderers
from alembic.operations import Operations

from sqlalchemy_declarative_extensions import role
from sqlalchemy_declarative_extensions.role.compare import (
    CreateRoleOp,
    DropRoleOp,
    UpdateRoleOp,
)
from sqlalchemy_declarative_extensions.role.ddl import (
    postgres_render_create_role,
    postgres_render_drop_role,
    postgres_render_update_role,
)

Operations.register_operation("create_role")(CreateRoleOp)
Operations.register_operation("update_role")(UpdateRoleOp)
Operations.register_operation("drop_role")(DropRoleOp)


@comparators.dispatch_for("schema")
def compare_roles(autogen_context, upgrade_ops, _):
    roles = autogen_context.metadata.info.get("roles")
    if not roles:
        return

    result = role.compare.compare_roles(autogen_context.connection, roles)
    upgrade_ops.ops[0:0] = result


@renderers.dispatch_for(CreateRoleOp)
def render_create_role(_, op: CreateRoleOp):
    role = op.role
    return (
        "op.create_role(\n"
        + f'    "{role.name}",\n'
        + "".join((f"    {key}={repr(value)},\n" for key, value in role.options))
        + ")"
    )


@renderers.dispatch_for(UpdateRoleOp)
def render_update_role(autogen_context, op: UpdateRoleOp):
    from_role = op.from_role
    to_role = op.to_role
    role_cls = type(to_role).__name__

    autogen_context.imports.add(
        f"from sqlalchemy_declarative_extensions.role import {role_cls}"
    )
    return (
        "op.update_role(\n"
        + f"    from_role={repr(from_role)},\n"
        + f"    to_role={repr(to_role)},\n"
        + ")"
    )


@renderers.dispatch_for(DropRoleOp)
def render_drop_role(_, op: DropRoleOp):
    role = op.role
    return f"op.drop_role('{role.name}')"


@Operations.implementation_for(CreateRoleOp)
def create_role(operations, op):
    command = postgres_render_create_role(op.role)
    operations.execute(command)


@Operations.implementation_for(UpdateRoleOp)
def update_role(operations, op):
    commands = postgres_render_update_role(op.from_role, op.to_role)
    for command in commands:
        operations.execute(command)


@Operations.implementation_for(DropRoleOp)
def drop_role(operations, op):
    command = postgres_render_drop_role(op.role)
    operations.execute(command)
