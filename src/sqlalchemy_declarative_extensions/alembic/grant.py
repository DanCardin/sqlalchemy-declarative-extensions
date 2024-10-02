from __future__ import annotations

from alembic.autogenerate.api import AutogenContext
from alembic.operations.ops import UpgradeOps

from sqlalchemy_declarative_extensions.alembic.base import (
    register_comparator_dispatcher,
    register_renderer_dispatcher,
    register_rewriter_dispatcher,
)
from sqlalchemy_declarative_extensions.grant import compare
from sqlalchemy_declarative_extensions.grant.base import Grants
from sqlalchemy_declarative_extensions.grant.compare import (
    GrantPrivilegesOp,
    Operation,
    RevokePrivilegesOp,
)
from sqlalchemy_declarative_extensions.role.base import Roles
from sqlalchemy_declarative_extensions.role.compare import RoleOp
from sqlalchemy_declarative_extensions.schema.compare import CreateSchemaOp


def compare_grants(autogen_context: AutogenContext, upgrade_ops: UpgradeOps, _):
    if autogen_context.connection is None:
        return  # pragma: no cover

    grants: Grants | None = Grants.extract(autogen_context.metadata)
    if not grants:
        return

    roles: Roles | None = Roles.extract(autogen_context.metadata)

    result = compare.compare_grants(autogen_context.connection, grants, roles=roles)
    if not result:
        return

    # Find the index of the last element of a role ops, which this needs to be after.
    last_role_index = -1
    for index, op in enumerate(upgrade_ops.ops):
        if isinstance(op, (CreateSchemaOp, RoleOp)):
            last_role_index = index

    # Insert after that point
    after_last_role_index = last_role_index + 1
    upgrade_ops.ops[after_last_role_index:after_last_role_index] = result  # type: ignore


def render_grant(_, op: Operation):
    return f'op.execute(sa.text("""{op.to_sql()}"""))'


register_comparator_dispatcher(compare_grants, target="schema")
register_renderer_dispatcher(GrantPrivilegesOp, RevokePrivilegesOp, fn=render_grant)
register_rewriter_dispatcher(GrantPrivilegesOp, RevokePrivilegesOp)
