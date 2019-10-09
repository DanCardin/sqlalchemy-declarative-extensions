import pytest
from pytest_mock_resources import create_postgres_fixture, PostgresConfig

pytest_plugins = "pytester"


pg = create_postgres_fixture(scope="function")


@pytest.fixture(scope="session")
def pmr_postgres_config():
    return PostgresConfig(port=None)
