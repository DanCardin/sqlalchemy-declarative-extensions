from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, text, types

from sqlalchemy_declarative_extensions import (
    declarative_database,
    register_sqlalchemy_events,
    view,
)
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True


class Foo(Base):
    __tablename__ = "foo"

    id = Column(types.String(), primary_key=True)


@view(Base)
class Bar:
    __tablename__ = "bar"
    __view__ = r"SELECT id::text FROM foo WHERE id like '\:foo %s %(id)s'"


register_sqlalchemy_events(Base.metadata, views=True)

pg = create_postgres_fixture(
    scope="function", engine_kwargs={"echo": True}, session=True
)


def test_escape_bindparam_postgres(pg):
    Base.metadata.create_all(bind=pg.connection())
    pg.commit()

    result = pg.execute(text("select * from bar")).fetchall()
    assert result == []
