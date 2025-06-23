import pytest
from pytest_mock_resources import PostgresConfig, create_postgres_fixture

_alembic_engine = create_postgres_fixture(scope="function")


@pytest.fixture
def alembic_engine(_alembic_engine):
    _alembic_engine.echo = True
    return _alembic_engine


@pytest.fixture(scope="session")
def pmr_postgres_config():
    return PostgresConfig(image="postgres:13", port=None, ci_port=None)
