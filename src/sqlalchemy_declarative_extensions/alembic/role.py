from __future__ import annotations

from alembic.autogenerate.api import AutogenContext

from sqlalchemy_declarative_extensions.alembic.base import (
    register_comparator_dispatcher,
    register_operation_dispatcher,
    register_renderer_dispatcher,
    register_rewriter_dispatcher,
)
from sqlalchemy_declarative_extensions.role.compare import (
    CreateRoleOp,
    DropRoleOp,
    Roles,
    UpdateRoleOp,
    compare_roles,
)


def _compare_roles(autogen_context: AutogenContext, upgrade_ops, _):
    roles: Roles | None = Roles.extract(autogen_context.metadata)
    if not roles:
        return

    assert autogen_context.connection
    result = compare_roles(autogen_context.connection, roles)
    upgrade_ops.ops[0:0] = result


def render_role(autogen_context: AutogenContext, op: CreateRoleOp):
    is_dynamic = op.role.is_dynamic
    if is_dynamic:
        autogen_context.imports.add("import os")

    return [
        f'op.execute({"f" if is_dynamic else ""}"""{command}""")'
        for command in op.to_sql(raw=False)
    ]


def execute_op(operations, op):
    commands = op.to_sql()
    for command in commands:
        operations.execute(command)


register_comparator_dispatcher(_compare_roles, target="schema")
register_renderer_dispatcher(CreateRoleOp, UpdateRoleOp, DropRoleOp, fn=render_role)
register_rewriter_dispatcher(CreateRoleOp, UpdateRoleOp, DropRoleOp)
register_operation_dispatcher(
    create_role=CreateRoleOp,
    update_role=UpdateRoleOp,
    drop_role=DropRoleOp,
    fn=execute_op,
)
