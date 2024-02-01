from pytest_mock_resources import create_postgres_fixture, create_sqlite_fixture
from sqlalchemy.sql.ddl import CreateSchema

from sqlalchemy_declarative_extensions import (
    Schemas,
    declarative_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.dialects import check_schema_exists
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    schemas = Schemas()


register_sqlalchemy_events(Base.metadata, schemas=True)

pg = create_postgres_fixture(scope="function", engine_kwargs={"echo": True})
sqlite = create_sqlite_fixture()


def test_createall_schema_pg(pg):
    with pg.begin() as conn:
        conn.execute(CreateSchema("foo"))

    Base.metadata.create_all(bind=pg)

    with pg.connect() as conn:
        assert check_schema_exists(conn, "foo") is False


def test_createall_schema_snowflake(snowflake):
    with snowflake.begin() as conn:
        conn.execute(CreateSchema("foo"))

    Base.metadata.create_all(bind=snowflake)

    with snowflake.connect() as conn:
        assert check_schema_exists(conn, "foo") is False
