from pytest_alembic import MigrationContext
from sqlalchemy import text


def test_apply_autogenerated_revision(alembic_runner: MigrationContext, alembic_engine):
    with alembic_engine.connect() as conn:
        conn.execute(text("create schema bar"))
        conn.execute(text("commit"))

    result = alembic_runner.generate_revision(
        autogenerate=True, prevent_file_generation=False
    )
    alembic_runner.migrate_up_one()

    with alembic_engine.connect() as conn:
        rows = conn.execute(
            text("select nspname from pg_namespace where nspname not like 'pg_%'")
        ).fetchall()

    result = [r for (r,) in rows]
    assert result == ["public", "information_schema", "foo"]
