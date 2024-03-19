import pytest
import sqlalchemy.exc
from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, text, types

from sqlalchemy_declarative_extensions import (
    Schemas,
    Views,
    declarative_database,
    register_sqlalchemy_events,
    view,
)
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base
from tests import skip_sqlalchemy13

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    schemas = Schemas().are("fooschema")
    views = Views(ignore=["fooschema.bar", "moo"])


class Foo(Base):
    __tablename__ = "foo"
    __table_args__ = {"schema": "fooschema"}

    id = Column(types.Integer(), primary_key=True)


@view(Base, register_as_model=True)
class Bar:
    __tablename__ = "bar"
    __table_args__ = {"schema": "fooschema"}
    __view__ = "select id from fooschema.foo where id < 10"

    id = Column(types.Integer(), primary_key=True)


@view(Base, register_as_model=True)
class Baz:
    __tablename__ = "baz"
    __table_args__ = {"schema": "fooschema"}
    __view__ = "select id from fooschema.foo where id < 10"

    id = Column(types.Integer(), primary_key=True)


register_sqlalchemy_events(Base.metadata, schemas=True, views=True, rows=True)

pg = create_postgres_fixture(
    scope="function", engine_kwargs={"echo": True}, session=True
)


@skip_sqlalchemy13
def test_ignore_views(pg):
    pg.execute(text("CREATE VIEW moo AS (SELECT rolname from pg_roles)"))

    Base.metadata.create_all(bind=pg.connection())

    pg.query(Baz).all()

    pg.execute(text("SELECT * FROM moo")).all()

    with pytest.raises(sqlalchemy.exc.ProgrammingError):
        pg.query(Bar).all()
