from pytest_mock_resources import (
    create_postgres_fixture,
    create_sqlite_fixture,
)
from sqlalchemy import Column, text, types

from sqlalchemy_declarative_extensions import (
    Row,
    Rows,
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

    rows = Rows().are(
        Row("foo", id=1),
        Row("foo", id=2),
        Row("foo", id=12),
        Row("foo", id=13),
    )


class Foo(Base):
    __tablename__ = "foo"

    id = Column(types.Integer(), primary_key=True)


view = View("bar", "select id from foo where id < 10")
register_view(Base.metadata, view)


register_sqlalchemy_events(Base.metadata, schemas=True, views=True, rows=True)

pg = create_postgres_fixture(
    scope="function", engine_kwargs={"echo": True}, session=True
)
sqlite = create_sqlite_fixture(scope="function", session=True)


def test_create_view_postgresql(pg):
    run_test(pg)


def test_create_view_sqlite(sqlite):
    run_test(sqlite)


def run_test(session):
    session.execute(text("CREATE TABLE foo (id integer)"))
    session.execute(text("CREATE VIEW bar AS SELECT id FROM foo WHERE id = 1"))
    session.execute(text("INSERT INTO foo (id) VALUES (1), (2), (12), (13)"))

    result = [f.id for f in session.execute(text("SELECT id from bar")).fetchall()]
    assert result == [1]

    Base.metadata.create_all(bind=session.connection())

    result = [f.id for f in session.execute(text("SELECT id from bar")).fetchall()]
    assert result == [1, 2]
