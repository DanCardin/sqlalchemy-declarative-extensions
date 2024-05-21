from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, text, types

from sqlalchemy_declarative_extensions import (
    Row,
    Rows,
    Schemas,
    declarative_database,
    register_sqlalchemy_events,
    register_view,
)
from sqlalchemy_declarative_extensions.dialects.postgresql import View
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

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


# Register imperitively
view = View(
    "bar",
    "select id from fooschema.foo where id < 10",
    schema="fooschema",
    materialized=True,
)

register_view(Base.metadata, view)


register_sqlalchemy_events(Base.metadata, schemas=True, views=True, rows=True)

pg = create_postgres_fixture(
    scope="function", engine_kwargs={"echo": True}, session=True
)


def test_create_view_postgresql(pg):
    pg.execute(text("CREATE SCHEMA fooschema"))
    pg.execute(text("CREATE TABLE fooschema.foo (id integer)"))

    pg.execute(
        text(
            "CREATE VIEW fooschema.bar AS (SELECT id FROM fooschema.foo WHERE id < 10)"
        )
    )

    Base.metadata.create_all(bind=pg.connection())

    result = [f.id for f in pg.query(Foo).all()]
    assert result == [1, 2, 12, 13]

    pg.execute(text("refresh materialized view fooschema.bar"))
    result = [f.id for f in pg.execute(text("select * from fooschema.bar")).fetchall()]
    assert result == [1, 2]
