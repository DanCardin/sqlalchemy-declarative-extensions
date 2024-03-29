from pytest_alembic import MigrationContext
from sqlalchemy import text


def test_apply_autogenerated_revision(alembic_runner: MigrationContext, alembic_engine):
    alembic_runner.migrate_up_one()
    alembic_runner.generate_revision(autogenerate=True, prevent_file_generation=False)
    alembic_runner.migrate_up_one()

    with alembic_engine.connect() as conn:
        result = conn.execute(text("select * from foo")).fetchall()

    expected_result = [
        (2, "asdf", None),
        (3, "qwer", False),
    ]
    assert expected_result == result
