import pytest
from pytest_mock_resources import create_postgres_fixture, PostgresConfig

_alembic_engine = create_postgres_fixture(scope="function")


@pytest.fixture
def alembic_engine(_alembic_engine):
    _alembic_engine.echo = True
    return _alembic_engine


@pytest.fixture(scope="session")
def pmr_postgres_config():
    return PostgresConfig(port=None, ci_port=None)
