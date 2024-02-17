import sqlalchemy
from pytest_mock_resources import create_postgres_fixture, create_sqlite_fixture

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

    schemas = Schemas().are("fooschema")


class Foo(Base):
    __tablename__ = "foo"
    __table_args__ = {"schema": "fooschema"}

    id = sqlalchemy.Column(
        sqlalchemy.types.Integer(), primary_key=True, autoincrement=False
    )


register_sqlalchemy_events(Base.metadata, schemas=True)

pg = create_postgres_fixture(scope="function", engine_kwargs={"echo": True})
sqlite = create_sqlite_fixture()


def test_createall_schema_pg(pg):
    Base.metadata.create_all(bind=pg)
    with pg.connect() as conn:
        result = conn.execute(Foo.__table__.select()).fetchall()
    assert result == []


def test_createall_schema_sqlite(sqlite):
    Base.metadata.create_all(bind=sqlite, checkfirst=False)
    with sqlite.connect() as conn:
        result = conn.execute(Foo.__table__.select()).fetchall()
    assert result == []


def test_createall_schema_snowflake(snowflake):
    Base.metadata.create_all(bind=snowflake, checkfirst=False)
    with snowflake.connect() as conn:
        result = conn.execute(Foo.__table__.select()).fetchall()
    assert result == []
