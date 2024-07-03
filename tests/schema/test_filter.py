import sqlalchemy
from pytest_mock_resources import create_postgres_fixture

from sqlalchemy_declarative_extensions import (
    Schemas,
    declarative_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    schemas = Schemas().are("foo", "foobar", "meow")


register_sqlalchemy_events(Base.metadata, schemas=["foo*"])

pg = create_postgres_fixture(scope="function", engine_kwargs={"echo": True})


def test_createall_schema_pg(pg):
    Base.metadata.create_all(bind=pg)
    with pg.connect() as conn:
        result = conn.execute(
            sqlalchemy.text(
                "SELECT nspname FROM pg_namespace where nspname not like 'pg%'"
            )
        ).fetchall()

    result = [s for (s,) in result]
    assert sorted(result) == ["foo", "foobar", "information_schema", "public"]
