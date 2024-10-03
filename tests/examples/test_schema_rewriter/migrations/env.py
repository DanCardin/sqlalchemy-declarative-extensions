import alembic.autogenerate
from alembic import context

# isort: split
from models import Base
from sqlalchemy import engine_from_config, pool

from sqlalchemy_declarative_extensions import register_alembic_events

register_alembic_events(schemas=True)


connectable = context.config.attributes.get("connection", None)
if connectable is None:
    connectable = engine_from_config(
        context.config.get_section(context.config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

with connectable.connect() as connection:
    context.configure(
        connection=connection,
        target_metadata=Base.metadata,
        process_revision_directives=alembic.autogenerate.rewriter.Rewriter(),
    )

    with context.begin_transaction():
        context.run_migrations()
