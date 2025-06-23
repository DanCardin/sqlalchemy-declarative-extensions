import pytest
from pytest_mock_resources import PostgresConfig, create_postgres_fixture
from sqlalchemy import func, select, text

from sqlalchemy_declarative_extensions import Functions, Schemas, Triggers, Views
from sqlalchemy_declarative_extensions.function.compare import compare_functions
from sqlalchemy_declarative_extensions.schema.compare import compare_schemas
from sqlalchemy_declarative_extensions.trigger.compare import compare_triggers
from sqlalchemy_declarative_extensions.view.compare import compare_views

pg = create_postgres_fixture(scope="function", engine_kwargs={"echo": True})


@pytest.fixture
def pmr_postgres_config():
    return PostgresConfig(image="postgis/postgis:13-3.5", port=None, ci_port=None)


@pytest.fixture(autouse=True)
def postgis_extension(pg):
    with pg.connect() as connection:
        connection.execute(text("CREATE EXTENSION postgis"))
        connection.execute(text("CREATE EXTENSION postgis_topology"))
        connection.commit()


def test_functions(pg):
    with pg.connect() as connection:
        diff = compare_functions(connection, Functions())
        result = connection.execute(select(func.PostGis_Version())).scalar()
        assert result
    assert diff == []


def test_schemas(pg):
    with pg.connect() as connection:
        diff = compare_schemas(connection, Schemas())
    assert diff == []


def test_triggers(pg):
    with pg.connect() as connection:
        diff = compare_triggers(connection, Triggers())
    assert diff == []


def test_views(pg):
    with pg.connect() as connection:
        diff = compare_views(connection, Views())
        result = connection.execute(
            text("SELECT * FROM geometry_columns")
        ).one_or_none()
        assert not result
    assert diff == []
