import sqlalchemy
from pytest_mock_resources import create_postgres_fixture, create_sqlite_fixture
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_declarative_extensions import (
    declarative_database,
    register_sqlalchemy_events,
    Schemas,
)

Base_ = declarative_base()


@declarative_database
class Base(Base_):
    __abstract__ = True

    schemas = Schemas().are("fooschema")


class Foo(Base):
    __tablename__ = "foo"
    __table_args__ = {"schema": "fooschema"}

    id = sqlalchemy.Column(sqlalchemy.types.Integer(), primary_key=True)


register_sqlalchemy_events(Base.metadata, schemas=True)

pg = create_postgres_fixture(scope="function", engine_kwargs={"echo": True})
sqlite = create_sqlite_fixture()


def test_createall_schema_pg(pg):
    Base.metadata.create_all(bind=pg)
    result = pg.execute(Foo.__table__.select()).fetchall()
    assert result == []


def test_createall_schema_sqlite(sqlite):
    Base.metadata.create_all(bind=sqlite, checkfirst=False)
    result = sqlite.execute(Foo.__table__.select()).fetchall()
    assert result == []
