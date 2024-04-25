from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, types

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
    )


class Foo(Base):
    __tablename__ = "foo"

    name = Column(types.Unicode(), primary_key=True)


register_sqlalchemy_events(Base.metadata, rows=True)

pg = create_postgres_fixture(engine_kwargs={"echo": True}, session=True)


def test_insert_missing(pg):
    Base.metadata.create_all(bind=pg.connection())

    result = pg.query(Foo).all()
    assert [r.name for r in result] == ["Foo :30s bar", "::::meow", r"\: \\::bar"]
