from alembic_utils.pg_materialized_view import PGMaterializedView
from alembic_utils.pg_view import PGView
from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, text, types
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_declarative_extensions import (
    Row,
    Rows,
    Schemas,
    Views,
    declarative_database,
    register_sqlalchemy_events,
)

Base_ = declarative_base()


@declarative_database
class Base(Base_):
    __abstract__ = True

    schemas = Schemas().are("fooschema")
    rows = Rows().are(
        Row("fooschema.foo", id=1),
        Row("fooschema.foo", id=2),
        Row("fooschema.foo", id=12),
        Row("fooschema.foo", id=13),
    )
    views = Views().are(
        PGView("fooschema", "bar", "select id from fooschema.foo where id > 10"),
        PGMaterializedView(
            "fooschema", "baz", "select id from fooschema.foo where id < 10"
        ),
    )


class Foo(Base):
    __tablename__ = "foo"
    __table_args__ = {"schema": "fooschema"}

    id = Column(types.Integer(), primary_key=True)


register_sqlalchemy_events(Base.metadata, schemas=True, views=True, rows=True)

pg = create_postgres_fixture(
    scope="function", engine_kwargs={"echo": True}, session=True
)


def test_create_view_postgresql(pg):
    Base.metadata.create_all(bind=pg.connection())

    result = [f.id for f in pg.query(Foo).all()]
    assert result == [1, 2, 12, 13]

    result = [f.id for f in pg.execute(text("select id from fooschema.bar")).all()]
    assert result == [12, 13]

    result = [f.id for f in pg.execute(text("select id from fooschema.baz")).all()]
    assert result == []

    pg.execute(text("refresh materialized view fooschema.baz"))
    result = [f.id for f in pg.execute(text("select id from fooschema.baz")).all()]
    assert result == [1, 2]
