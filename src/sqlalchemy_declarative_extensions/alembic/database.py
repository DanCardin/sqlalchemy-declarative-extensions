from __future__ import annotations

from alembic.autogenerate.api import AutogenContext

from sqlalchemy_declarative_extensions import database
from sqlalchemy_declarative_extensions.alembic.base import (
    register_comparator_dispatcher,
    register_renderer_dispatcher,
    register_rewriter_dispatcher,
)
from sqlalchemy_declarative_extensions.database.base import Databases
from sqlalchemy_declarative_extensions.database.compare import (
    CreateDatabaseOp,
    DatabaseOp,
    DropDatabaseOp,
)


def compare_databases(autogen_context: AutogenContext, upgrade_ops, _):
    assert autogen_context.metadata
    databases: Databases | None = autogen_context.metadata.info.get("databases")
    if not databases:
        return

    assert autogen_context.connection
    result = database.compare.compare_databases(autogen_context.connection, databases)
    upgrade_ops.ops[0:0] = result


def render_database(autogen_context: AutogenContext, op: DatabaseOp):
    return [f'op.execute("{command}")' for command in op.to_sql()]


register_comparator_dispatcher(compare_databases, target="database")
register_renderer_dispatcher(CreateDatabaseOp, DropDatabaseOp, fn=render_database)
register_rewriter_dispatcher(CreateDatabaseOp, DropDatabaseOp)
