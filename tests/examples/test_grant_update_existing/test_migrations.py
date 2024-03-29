import pytest
import sqlalchemy.exc
from pytest_alembic import MigrationContext, tests
from sqlalchemy import text

from sqlalchemy_declarative_extensions.dialects import get_roles


def test_apply_autogenerated_revision(alembic_runner: MigrationContext, alembic_engine):
    alembic_runner.migrate_up_one()

    with alembic_engine.connect() as conn:
        conn.execute(
            text(
                "alter default privileges in schema public grant select on tables to o2_read"
            )
        )
        conn.execute(
            text(
                "alter default privileges in schema public grant insert, update, delete on tables to o2_write"
            )
        )
        conn.execute(
            text(
                "alter default privileges in schema public grant usage on sequences to o2_write"
            )
        )

    result = alembic_runner.generate_revision(
        autogenerate=True, prevent_file_generation=False
    )
    alembic_runner.migrate_up_one()

    # Verify this no longer sees changes to make! Failing here would imply the autogenerate
    # is not fully normalizing the difference.
    tests.test_model_definitions_match_ddl(alembic_runner)

    with alembic_engine.connect() as conn:
        result = [r.name for r in get_roles(conn, exclude=["user"])]

        expected_result = [
            "o1_app",
            "o2_read",
            "o2_write",
        ]
        assert expected_result == result

        # only "o2_read" can read
        conn.execute(text("SET ROLE o2_read; SELECT * FROM foo"))
        conn.execute(text("SET ROLE o2_read; INSERT INTO foo VALUES (DEFAULT)"))
        conn.execute(text("SET ROLE o2_read; UPDATE foo set id=DEFAULT"))
        conn.execute(text("SET ROLE o2_read; DELETE FROM foo"))

    with alembic_engine.connect() as conn:
        # "o2_write" can **not** read or write because it should have been revoked
        with pytest.raises(sqlalchemy.exc.ProgrammingError):
            conn.execute(text("SET ROLE o2_write; SELECT * FROM created_at"))

    with alembic_engine.connect() as conn:
        with pytest.raises(sqlalchemy.exc.ProgrammingError):
            conn.execute(text("SET ROLE o2_write; INSERT INTO foo VALUES (DEFAULT)"))

    with alembic_engine.connect() as conn:
        # "o1_app" can do the same things as o2_read
        conn.execute(text("SET ROLE o1_app; SELECT * FROM foo"))
        conn.execute(text("SET ROLE o1_app; INSERT INTO foo VALUES (DEFAULT)"))
        conn.execute(text("SET ROLE o1_app; UPDATE foo set id=DEFAULT"))
        conn.execute(text("SET ROLE o1_app; DELETE FROM foo"))
