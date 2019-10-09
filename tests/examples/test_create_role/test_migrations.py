from pytest_alembic import MigrationContext

from sqlalchemy_declarative_extensions.role import PGRole
from sqlalchemy_declarative_extensions.role.compare import get_existing_roles_postgresql


def test_apply_autogenerated_revision(alembic_runner: MigrationContext, alembic_engine):
    result = alembic_runner.generate_revision(
        autogenerate=True, prevent_file_generation=False
    )
    alembic_runner.migrate_up_one()

    result = get_existing_roles_postgresql(
        alembic_engine, exclude=[alembic_engine.pmr_credentials.username]
    )

    expected_result = [
        PGRole(
            "admin",
            superuser=True,
            createdb=True,
            createrole=True,
            login=False,
            replication=True,
            bypass_rls=True,
            in_roles=["read", "write"],
        ),
        PGRole(
            "app",
            login=True,
            in_roles=["read", "write"],
        ),
        PGRole("read"),
        PGRole("write"),
    ]
    assert expected_result == result
