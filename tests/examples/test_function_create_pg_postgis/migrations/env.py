from alembic import context

# isort: split
from models import Base
from sqlalchemy import engine_from_config, pool

from sqlalchemy_declarative_extensions import register_alembic_events

target_metadata = Base.metadata

register_alembic_events(views=True, rows=True)

connectable = context.config.attributes.get("connection", None)

if connectable is None:
    connectable = engine_from_config(
        context.config.get_section(context.config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

IGNORE_TABLES = ["spatial_ref_sys", "layer", "topology"]


def include_object(item, name, item_type, reflected, compare_to) -> bool:
    if item_type == "table" and name in IGNORE_TABLES:
        return False
    return True


with connectable.connect() as connection:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()
