def register_alembic_events(
    schemas: bool = True,
    roles: bool = True,
    grants: bool = True,
    rows: bool = True,
):
    """Register handlers into alembic's event system for the supported object types.

    By default all object types are enabled, but each can be individually disabled.

    Note this is the opposite of the defaults when registering against SQLAlchemy's
    event system.
    """
    if schemas:
        import sqlalchemy_declarative_extensions.alembic.schema  # noqa

    if roles:
        import sqlalchemy_declarative_extensions.alembic.role  # noqa

    if grants:
        import sqlalchemy_declarative_extensions.alembic.grant  # noqa

    if rows:
        import sqlalchemy_declarative_extensions.alembic.row  # noqa
