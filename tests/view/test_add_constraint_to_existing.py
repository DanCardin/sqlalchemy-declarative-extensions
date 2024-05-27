from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, UniqueConstraint, text, types

from sqlalchemy_declarative_extensions import (
    Row,
    Rows,
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

    rows = Rows().are(
        Row("foo", id=1),
        Row("foo", id=2),
        Row("foo", id=12),
        Row("foo", id=13),
    )


class Foo(Base):
    __tablename__ = "foo"

    id = Column(types.Integer(), primary_key=True)


# Register imperitively
view = View(
    "bar",
    "select foo.id from foo where foo.id < 10",
    constraints=[UniqueConstraint("id")],
    materialized=True,
)

register_view(Base.metadata, view)


register_sqlalchemy_events(Base.metadata, schemas=True, views=True, rows=True)

pg = create_postgres_fixture(
    scope="function", engine_kwargs={"echo": True}, session=True
)


def test_create_view_postgresql(pg):
    pg.execute(text("CREATE TABLE foo (id integer)"))
    pg.execute(
        text(
            "CREATE MATERIALIZED VIEW bar AS (SELECT foo.id FROM foo WHERE foo.id < 10)"
        )
    )

    Base.metadata.create_all(bind=pg.connection())

    result = [f.id for f in pg.query(Foo).all()]
    assert result == [1, 2, 12, 13]

    pg.execute(text("refresh materialized view bar"))
    result = [f.id for f in pg.execute(text("select * from bar")).fetchall()]
    assert result == [1, 2]
