from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, text, types

from sqlalchemy_declarative_extensions import (
    declarative_database,
    register_sqlalchemy_events,
    view,
)
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base, select

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True


class Foo(Base):
    __tablename__ = "foo"
    id = Column(types.Integer(), primary_key=True)


@view(Base)
class HighFoo:
    __tablename__ = "high_foo"

    @staticmethod
    def __view__():
        return select(Foo.__table__).where(Foo.__table__.c.id >= 10)


register_sqlalchemy_events(Base.metadata, schemas=True, views=True, rows=True)

pg = create_postgres_fixture(
    scope="function", engine_kwargs={"echo": True}, session=True
)


def test_created_together(pg):
    Base.metadata.create_all(pg.connection())

    for i in range(8, 12):
        pg.add(Foo(id=i))
    pg.commit()

    result = [i for (i,) in pg.execute(text('select id from "high_foo"'))]
    assert result == [10, 11]
