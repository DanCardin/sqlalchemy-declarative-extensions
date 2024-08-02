from typing import Optional

from alembic.autogenerate.api import AutogenContext
from alembic.autogenerate.compare import comparators
from alembic.autogenerate.render import renderers
from alembic.operations.ops import UpgradeOps

from sqlalchemy_declarative_extensions.grant import compare
from sqlalchemy_declarative_extensions.grant.base import Grants
from sqlalchemy_declarative_extensions.grant.compare import (
    GrantPrivilegesOp,
    RevokePrivilegesOp,
)
from sqlalchemy_declarative_extensions.role.base import Roles
from sqlalchemy_declarative_extensions.role.compare import RoleOp, UseRoleOp
from sqlalchemy_declarative_extensions.schema.compare import CreateSchemaOp


@comparators.dispatch_for("schema")
def compare_grants(autogen_context: AutogenContext, upgrade_ops: UpgradeOps, _):
    if autogen_context.metadata is None or autogen_context.connection is None:
        return  # pragma: no cover

    grants: Optional[Grants] = autogen_context.metadata.info.get("grants")
    if not grants:
        return

    roles: Optional[Roles] = autogen_context.metadata.info.get("roles")

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


@renderers.dispatch_for(GrantPrivilegesOp)
@renderers.dispatch_for(RevokePrivilegesOp)
def render_grant(_, op: GrantPrivilegesOp | RevokePrivilegesOp | UseRoleOp):
    return [f'op.execute("""{command}""")' for command in op.to_sql()]
