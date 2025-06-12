import pytest
from pytest_mock_resources import PostgresConfig, create_postgres_fixture

alembic_engine = create_postgres_fixture(scope="function", engine_kwargs={"echo": True})


@pytest.fixture(scope="session")
def pmr_postgres_config():
    return PostgresConfig(image="postgres:13", port=None, ci_port=None)
