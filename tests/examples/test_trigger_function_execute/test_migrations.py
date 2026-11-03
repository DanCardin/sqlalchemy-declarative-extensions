from pathlib import Path

import pytest
from pytest_alembic import MigrationContext
from pytest_mock_resources import PostgresConfig, create_postgres_fixture
from sqlalchemy import text

alembic_engine = create_postgres_fixture(scope="function", engine_kwargs={"echo": True})


@pytest.fixture(scope="session")
def pmr_postgres_config():
    return PostgresConfig(image="postgres:13", port=None, ci_port=None)


def test_function_is_created_before_triggers_and_dropped_after(
    alembic_runner: MigrationContext, alembic_engine
):
    alembic_runner.generate_revision(autogenerate=True, prevent_file_generation=False)

    (revision,) = Path("migrations/versions").glob("*.py")
    source = revision.read_text()
    upgrade, downgrade = source.split("def downgrade")
    assert upgrade.count("CREATE FUNCTION") == 1
    assert upgrade.index("CREATE FUNCTION") < upgrade.index("CREATE TRIGGER")
    assert downgrade.index("DROP TRIGGER") < downgrade.index("DROP FUNCTION")

    alembic_runner.migrate_up_one()

    with alembic_engine.connect() as conn:
        conn.execute(text("insert into foo (id) values (1)"))
        conn.execute(text("insert into bar (id) values (10)"))
        conn.commit()
        result = [r for r, *_ in conn.execute(text("select id from log")).fetchall()]

    assert sorted(result) == [2, 11]

    alembic_runner.migrate_down_one()
