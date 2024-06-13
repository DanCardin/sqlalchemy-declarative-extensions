from __future__ import annotations

from alembic.autogenerate.api import AutogenContext
from alembic.autogenerate.compare import comparators
from alembic.autogenerate.render import renderers

from sqlalchemy_declarative_extensions import database
from sqlalchemy_declarative_extensions.database.base import Databases
from sqlalchemy_declarative_extensions.database.compare import (
    CreateDatabaseOp,
    DropDatabaseOp,
)


@comparators.dispatch_for("database")
def compare_databases(autogen_context: AutogenContext, upgrade_ops, _):
    assert autogen_context.metadata
    databases: Databases | None = autogen_context.metadata.info.get("databases")
    if not databases:
        return

    assert autogen_context.connection
    result = database.compare.compare_databases(autogen_context.connection, databases)
    upgrade_ops.ops[0:0] = result


@renderers.dispatch_for(CreateDatabaseOp)
@renderers.dispatch_for(DropDatabaseOp)
def render_create_database(autogen_context: AutogenContext, op: CreateDatabaseOp):
    return [f'op.execute("{command}")' for command in op.to_sql()]
