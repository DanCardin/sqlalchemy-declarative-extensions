import pytest
from pytest_mock_resources import create_postgres_fixture, PostgresConfig
from pytest_mock_resources.container.base import get_container

pytest_plugins = "pytester"


def pytest_sessionstart(session):
    workerinput = getattr(session.config, "workerinput", None)
    if workerinput is not None:
        import coverage

        coverage.process_startup()


pg = create_postgres_fixture(scope="function", engine_kwargs={"echo": True})


@pytest.fixture
def pmr_postgres_container(pytestconfig, pmr_postgres_config: PostgresConfig):
    yield from get_container(pytestconfig, pmr_postgres_config)


@pytest.fixture
def pmr_postgres_config():
    return PostgresConfig(port=None)
