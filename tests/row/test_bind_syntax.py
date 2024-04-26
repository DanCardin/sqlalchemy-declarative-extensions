from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, text, types

from sqlalchemy_declarative_extensions import (
    Row,
    Rows,
    declarative_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    rows = Rows().are(
        Row("foo", name="Foo :30s bar"),
        Row("foo", name="::::meow"),
        Row("foo", name=r"\: \\::bar"),
        Row("foo", name=r":foo"),
        Row("foo", name=r"100%"),
    )


class Foo(Base):
    __tablename__ = "foo"

    name = Column(types.Unicode(), primary_key=True)


register_sqlalchemy_events(Base.metadata, rows=True)

pg = create_postgres_fixture(engine_kwargs={"echo": True}, session=True)


def test_insert_missing(pg):
    pg.execute(text("CREATE TABLE foo (name VARCHAR PRIMARY KEY)"))
    pg.execute(text(r"insert into foo (name) values ('\:foo')"))
    pg.execute(text(r"insert into foo (name) values ('100%')"))

    Base.metadata.create_all(bind=pg.connection())

    result = pg.query(Foo).all()
    assert [r.name for r in result] == [
        ":foo",
        "100%",
        "Foo :30s bar",
        "::::meow",
        r"\: \\::bar",
    ]
