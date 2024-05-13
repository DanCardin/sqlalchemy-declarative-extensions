from pytest_mock_resources import (
    create_postgres_fixture,
    create_sqlite_fixture,
)
from sqlalchemy import Column, text, types

from sqlalchemy_declarative_extensions import (
    Row,
    Rows,
    Schemas,
    View,
    declarative_database,
    register_sqlalchemy_events,
    register_view,
)
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
)

register_view(Base.metadata, view)


register_sqlalchemy_events(Base.metadata, schemas=True, views=True, rows=True)

pg = create_postgres_fixture(
    scope="function", engine_kwargs={"echo": True}, session=True
)
sqlite = create_sqlite_fixture(scope="function", session=True)


def test_create_view_postgresql(pg):
    pg.execute(text("CREATE SCHEMA fooschema"))
    run_test(pg)


def test_create_view_sqlite(sqlite):
    sqlite.execute(text("ATTACH DATABASE ':memory:' AS fooschema"))
    run_test(sqlite)


def run_test(session):
    session.execute(text("CREATE TABLE fooschema.foo (id integer)"))
    session.execute(
        text("CREATE VIEW fooschema.bar AS SELECT id FROM fooschema.foo WHERE id = 1")
    )
    session.execute(text("INSERT INTO fooschema.foo (id) VALUES (1), (2), (12), (13)"))
    session.commit()

    result = [
        f.id for f in session.execute(text("SELECT id from fooschema.bar")).fetchall()
    ]
    assert result == [1]

    Base.metadata.create_all(bind=session.connection())

    result = [
        f.id for f in session.execute(text("SELECT id from fooschema.bar")).fetchall()
    ]
    assert result == [1, 2]
