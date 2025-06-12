import logging
import os

import pytest
from pytest_mock_resources import MysqlConfig, PostgresConfig, create_postgres_fixture
from pytest_mock_resources.container.base import get_container

# isort: split
# XXX: Deal with python 3.8-specific reload issue due to the `sys.modules` hack below.
import pydantic

assert pydantic

pytest_plugins = "pytester"


def pytest_sessionstart(session):
    logging.basicConfig()

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
    return PostgresConfig(image="postgres:13", port=None, ci_port=None)


@pytest.fixture
def pmr_mysql_container(pytestconfig, pmr_mysql_config):
    yield from get_container(pytestconfig, pmr_mysql_config)


@pytest.fixture
def pmr_mysql_config():
    return MysqlConfig(image="mysql:8", port=None, ci_port=None)


@pytest.fixture
def snowflake():
    try:
        import fakesnow
        import snowflake.sqlalchemy  # noqa
        from snowflake.sqlalchemy import URL
    except ImportError:
        pytest.skip("Snowflake not installed")
        return

    from sqlalchemy.engine.create import create_engine

    with fakesnow.patch(
        create_database_on_connect=True,
        create_schema_on_connect=False,
    ):
        engine = create_engine(
            URL(account="test", database="test", schema="information_schema")
        )
        yield engine


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
    import sys

    from alembic.autogenerate.compare import comparators
    from alembic.autogenerate.render import renderers
    from alembic.autogenerate.rewriter import Rewriter
    from alembic.operations import Operations

    reg = comparators._registry
    clean_registry = [
        fn
        for fn in reg[("schema", "default")]
        if not fn.__module__.startswith("sqlalchemy_declarative_extensions")
    ]

    reg[("schema", "default")] = clean_registry

    containers = [renderers, Operations._to_impl, Rewriter._traverse]
    for container in containers:
        container._registry = {
            (op, k): v
            for (op, k), v in container._registry.items()
            if not op.__module__.startswith("sqlalchemy_declarative_extensions")
        }

    objects = [
        "database",
        "function",
        "grant",
        "procedure",
        "role",
        "row",
        "schema",
        "trigger",
        "view",
    ]
    for obj in objects:
        sys.modules.pop(f"sqlalchemy_declarative_extensions.alembic.{obj}", None)
