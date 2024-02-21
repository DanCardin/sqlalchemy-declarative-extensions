from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, text, types

from sqlalchemy_declarative_extensions import (
    Row,
    Rows,
    Schemas,
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
    rows = Rows().are(
        Row("fooschema.foo", id=1),
        Row("fooschema.foo", id=2),
        Row("fooschema.foo", id=12),
        Row("fooschema.foo", id=13),
    )


class Foo(Base):
    __tablename__ = "foo"
    __table_args__ = {"schema": "fooschema"}

    id = Column(types.Integer(), primary_key=True)


@view(Base, materialized=True, register_as_model=True)
class Bar:
    __tablename__ = "bar"
    __table_args__ = ({"schema": "fooschema"},)
    __view__ = "select id from fooschema.foo where id < 10"

    id = Column(types.Integer(), primary_key=True)


register_sqlalchemy_events(Base.metadata, schemas=True, views=True, rows=True)

pg = create_postgres_fixture(
    scope="function", engine_kwargs={"echo": True}, session=True
)


@skip_sqlalchemy13
def test_create_view_postgresql(pg):
    Base.metadata.create_all(bind=pg.connection())

    result = [f.id for f in pg.query(Foo).all()]
    assert result == [1, 2, 12, 13]

    result = [f.id for f in pg.query(Bar).all()]
    assert result == []

    pg.execute(text("refresh materialized view fooschema.bar"))
    result = [f.id for f in pg.query(Bar).all()]
    assert result == [1, 2]
