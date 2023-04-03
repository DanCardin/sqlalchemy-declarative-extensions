def register_alembic_events(
    schemas: bool = True,
    views: bool = True,
    roles: bool = True,
    grants: bool = True,
    functions: bool = True,
    triggers: bool = True,
    rows: bool = True,
):
    """Register handlers into alembic's event system for the supported object types.

    By default all object types are enabled, but each can be individually disabled.

    Note this is the opposite of the defaults when registering against SQLAlchemy's
    event system.
    """
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

    if triggers:
        import sqlalchemy_declarative_extensions.alembic.trigger

    if rows:
        import sqlalchemy_declarative_extensions.alembic.row  # noqa
