from alembic.autogenerate.compare import comparators
from alembic.autogenerate.render import renderers
from alembic.operations import Operations

from sqlalchemy_declarative_extensions import grant
from sqlalchemy_declarative_extensions.grant.base import Grants
from sqlalchemy_declarative_extensions.grant.compare import (
    GrantPrivilegesOp,
    RevokePrivilegesOp,
)


@comparators.dispatch_for("schema")
def compare_grants(autogen_context, upgrade_ops, _):
    grants: Grants = autogen_context.metadata.info.get("grants")
    if not grants:
        return

    result = grant.compare.compare_grants(autogen_context.connection, grants)
    upgrade_ops.ops.extend(result)


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
