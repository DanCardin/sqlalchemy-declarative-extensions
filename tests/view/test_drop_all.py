from pytest_mock_resources import (
    create_postgres_fixture,
)
from sqlalchemy import Column, types

from sqlalchemy_declarative_extensions import (
    Row,
    Rows,
    declarative_database,
    register_sqlalchemy_events,
    view,
)
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base, select

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


foo_table = Foo.__table__


@view(Base, register_as_model=True)
class Bar:
    __tablename__ = "bar"
    __view__ = select(foo_table.c.id).where(foo_table.c.id > 10)

    id = Column(types.Integer(), primary_key=True)


register_sqlalchemy_events(Base.metadata, schemas=True, views=True, rows=True)

pg = create_postgres_fixture(
    scope="function", engine_kwargs={"echo": True}, session=True
)


def test_create_view_postgresql(pg):
    Base.metadata.create_all(bind=pg.connection())
    Base.metadata.drop_all(bind=pg.connection())
