from typing import Optional

from alembic.autogenerate.api import AutogenContext
from alembic.autogenerate.compare import comparators
from alembic.autogenerate.render import renderers
from alembic.operations import Operations
from alembic.operations.ops import UpgradeOps

from sqlalchemy_declarative_extensions.grant import compare
from sqlalchemy_declarative_extensions.grant.base import Grants
from sqlalchemy_declarative_extensions.grant.compare import (
    GrantPrivilegesOp,
    RevokePrivilegesOp,
)
from sqlalchemy_declarative_extensions.role.compare import RoleOp


@comparators.dispatch_for("schema")
def compare_grants(autogen_context: AutogenContext, upgrade_ops: UpgradeOps, _):
    if autogen_context.metadata is None or autogen_context.connection is None:
        return

    grants: Optional[Grants] = autogen_context.metadata.info.get("grants")
    if not grants:
        return

    result = compare.compare_grants(autogen_context.connection, grants)
    if not result:
        return

    # Find the index of the last element of a role ops, which this needs to be after.
    last_role_index = -1
    for index, op in enumerate(upgrade_ops.ops):
        if isinstance(op, RoleOp):
            last_role_index = index

    # Insert after that point
    after_last_role_index = last_role_index + 1
    upgrade_ops.ops[after_last_role_index:after_last_role_index] = result  # type: ignore


Operations.register_operation("grant_privileges")(GrantPrivilegesOp)
Operations.register_operation("revoke_privileges")(RevokePrivilegesOp)


@renderers.dispatch_for(GrantPrivilegesOp)
def render_grant(autogen_context, op):
    return f'op.grant_privileges(sa.text("{op.grant.to_sql()}"))'


@renderers.dispatch_for(RevokePrivilegesOp)
def render_revoke(autogen_context, op):
    return f'op.revoke_privileges(sa.text("{op.grant.to_sql()}"))'


@Operations.implementation_for(GrantPrivilegesOp)
def grant_op(operations, op):
    operations.execute(op.grant)


@Operations.implementation_for(RevokePrivilegesOp)
def revoke_op(operations, op):
    operations.execute(op.grant)
