from alembic.autogenerate.api import AutogenContext
from alembic.autogenerate.compare import comparators
from alembic.autogenerate.render import renderers
from alembic.operations import Operations

from sqlalchemy_declarative_extensions.view.compare import (
    CreateViewOp,
    DropViewOp,
    compare_views,
)

Operations.register_operation("create_view")(CreateViewOp)
Operations.register_operation("drop_view")(DropViewOp)


@comparators.dispatch_for("schema")
def _compare_views(autogen_context, upgrade_ops, _):
    views = autogen_context.metadata.info.get("views")
    if not views:
        return

    result = compare_views(autogen_context.connection, views)
    upgrade_ops.ops.extend(result)


@renderers.dispatch_for(CreateViewOp)
def render_create_view(autogen_context: AutogenContext, op: CreateViewOp):
    assert autogen_context.connection
    dialect = autogen_context.connection.dialect
    command = op.view.render_definition(dialect)

    schema_part = ""
    if op.view.schema:
        schema_part = f'", schema={op.view.schema}"'
    return f'op.create_view("{op.view.name}", """{command}"""{schema_part})'


@renderers.dispatch_for(DropViewOp)
def render_drop_view(autogen_context: AutogenContext, op: DropViewOp):
    schema_part = ""
    if op.view.schema:
        schema_part = f'", schema={op.view.schema}"'
    return f'op.drop_view("{op.view.name}"{schema_part})'


@Operations.implementation_for(CreateViewOp)
def create_view(operations, op: CreateViewOp):
    dialect = operations.migration_context.connection.dialect
    command = op.to_sql(dialect)
    operations.execute(command)


@Operations.implementation_for(DropViewOp)
def drop_view(operations, op: DropViewOp):
    command = op.to_sql()
    operations.execute(command)
