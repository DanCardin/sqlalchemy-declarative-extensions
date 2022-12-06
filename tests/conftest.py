import os

import pytest
from pytest_mock_resources import MysqlConfig, PostgresConfig, create_postgres_fixture
from pytest_mock_resources.container.base import get_container

pytest_plugins = "pytester"


def pytest_sessionstart(session):
    workerinput = getattr(session.config, "workerinput", None)
    if workerinput is not None:
        import coverage

        coverage.process_startup()

    os.environ["PYTHONUNBUFFERED"] = "1"


pg = create_postgres_fixture(scope="function", engine_kwargs={"echo": True})


@pytest.fixture
def pmr_postgres_container(pytestconfig, pmr_postgres_config: PostgresConfig):
    yield from get_container(pytestconfig, pmr_postgres_config)


@pytest.fixture
def pmr_postgres_config():
    return PostgresConfig(port=None, ci_port=None)


@pytest.fixture
def pmr_mysql_container(pytestconfig, pmr_mysql_config: MysqlConfig):
    yield from get_container(pytestconfig, pmr_mysql_config)


@pytest.fixture
def pmr_mysql_config():
    return MysqlConfig(image="mysql:8", port=None, ci_port=None)


@pytest.fixture(autouse=True)
def clear_registry():
    """Clear out state accumulated by importing alembic modules in env.pys.

    We are running pytester pytest invocations of alembic "inline", i.e.
    in the current process. When run as a subprocess,
    coverage's coverage reporting is unreliable, even following their subprocess
    collection documentation.

    Due to the inline execution, alembic is designed in such a way that it accumulates
    registry state that double-registers our handlers and causes tests to fail.

    Additionally, clearing out that state requires that we "un-import" those modules
    so that they'll be reliably re-registered on subsequent tests.

    This is ultimately multiprocess-safe with xdist, because each xdist worker
    is executing tests serially, so we can assume it's safe to mutate global state
    in between tests.
    """
    from alembic.autogenerate.compare import comparators
    from alembic.autogenerate.render import renderers
    from alembic.operations import Operations

    reg = comparators._registry
    clean_registry = [
        fn
        for fn in reg[("schema", "default")]
        if not fn.__module__.startswith("sqlalchemy_declarative_extensions")
    ]

    reg[("schema", "default")] = clean_registry

    renderers._registry = {
        (op, k): v
        for (op, k), v in renderers._registry.items()
        if not op.__module__.startswith("sqlalchemy_declarative_extensions")
    }
    Operations._to_impl._registry = {
        (op, k): v
        for (op, k), v in Operations._to_impl._registry.items()
        if not op.__module__.startswith("sqlalchemy_declarative_extensions")
    }

    import sys

    sys.modules.pop("sqlalchemy_declarative_extensions.alembic.schema", None)
    sys.modules.pop("sqlalchemy_declarative_extensions.alembic.role", None)
    sys.modules.pop("sqlalchemy_declarative_extensions.alembic.grant", None)
    sys.modules.pop("sqlalchemy_declarative_extensions.alembic.row", None)
    sys.modules.pop("sqlalchemy_declarative_extensions.alembic.view", None)
