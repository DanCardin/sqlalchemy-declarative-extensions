from __future__ import annotations


def register_alembic_events(
    *,
    databases: bool = True,
    schemas: bool = True,
    views: bool = True,
    roles: bool = True,
    grants: bool = True,
    functions: bool = True,
    procedures: bool = True,
    triggers: bool = True,
    rows: bool = True,
):
    """Register handlers into alembic's event system for the supported object types.

    By default all object types are enabled, but each can be individually disabled.

    Note this is the opposite of the defaults when registering against SQLAlchemy's
    event system.
    """
    if databases:
        import sqlalchemy_declarative_extensions.alembic.database

    if schemas:
        import sqlalchemy_declarative_extensions.alembic.schema

    if views:
        import sqlalchemy_declarative_extensions.alembic.view

    if roles:
        import sqlalchemy_declarative_extensions.alembic.role

    if grants:
        import sqlalchemy_declarative_extensions.alembic.grant

    if functions:
        import sqlalchemy_declarative_extensions.alembic.function

    if procedures:
        import sqlalchemy_declarative_extensions.alembic.procedure

    if triggers:
        import sqlalchemy_declarative_extensions.alembic.trigger

    if rows:
        import sqlalchemy_declarative_extensions.alembic.row  # noqa


def _traverse_any_directive(self, context, revision, directive) -> None:
    pass


def register_comparator_dispatcher(fn, target: str):
    from alembic.autogenerate.compare import comparators

    dispatcher = comparators.dispatch_for(target)
    dispatcher(fn)


def register_renderer_dispatcher(*ops, fn):
    from alembic.autogenerate.render import renderers

    for op in ops:
        dispatcher = renderers.dispatch_for(op)
        dispatcher(fn)


def register_rewriter_dispatcher(*ops):
    from alembic.autogenerate.rewriter import Rewriter

    for op in ops:
        dispatcher = Rewriter._traverse.dispatch_for(op)
        dispatcher(_traverse_any_directive)


def register_operation_dispatcher(*, fn, **ops):
    from alembic.operations import Operations

    for operation_name, op in ops.items():
        operation_dispatcher = Operations.register_operation(operation_name)
        operation_dispatcher(op)

        implementation_dispatcher = Operations.implementation_for(op)
        implementation_dispatcher(fn)
