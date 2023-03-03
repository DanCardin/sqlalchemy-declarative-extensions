from alembic import context

# isort: split
from models import Base
from sqlalchemy import engine_from_config, pool

from sqlalchemy_declarative_extensions import register_alembic_events

target_metadata = Base.metadata

register_alembic_events(schemas=True, views=True, rows=True)

connectable = context.config.attributes.get("connection", None)

if connectable is None:
    connectable = engine_from_config(
        context.config.get_section(context.config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

with connectable.connect() as connection:
    context.configure(
        connection=connection, target_metadata=target_metadata, include_schemas=True
    )

    with context.begin_transaction():
        context.run_migrations()
