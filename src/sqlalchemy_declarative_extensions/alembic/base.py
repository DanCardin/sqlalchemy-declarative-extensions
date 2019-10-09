def register_alembic_events(
    schemas: bool = True,
    roles: bool = True,
    grants: bool = True,
    models=True,
):
    if schemas:
        import sqlalchemy_declarative_extensions.alembic.schema  # noqa

    if roles:
        import sqlalchemy_declarative_extensions.alembic.role  # noqa

    if grants:
        import sqlalchemy_declarative_extensions.alembic.grant  # noqa

    if models:
        import sqlalchemy_declarative_extensions.alembic.model  # noqa
