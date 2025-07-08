from pytest_mock_resources import (
    create_mysql_fixture,
    create_postgres_fixture,
    create_sqlite_fixture,
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
from tests import skip_sqlalchemy13

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


@view(Base, register_as_model=True)
class Baz:
    __tablename__ = "baz"
    __view__ = select(foo_table.c.id).where(foo_table.c.id < 10)

    id = Column(types.Integer(), primary_key=True)


register_sqlalchemy_events(Base.metadata, schemas=False, views=True, rows=True)

pg = create_postgres_fixture(
    scope="function", engine_kwargs={"echo": True}, session=True
)
sqlite = create_sqlite_fixture(scope="function", session=True)
mysql = create_mysql_fixture(scope="function", session=True)


@skip_sqlalchemy13
def test_create_view_postgresql(pg):
    run_test(pg)


@skip_sqlalchemy13
def test_create_view_mysql(mysql):
    run_test(mysql)


@skip_sqlalchemy13
def test_create_view_sqlite(sqlite):
    run_test(sqlite)


def run_test(session):
    Base.metadata.create_all(bind=session.connection())
    session.commit()

    result = [f.id for f in session.query(Foo).all()]
    assert result == [1, 2, 12, 13]

    result = [f.id for f in session.query(Bar).all()]
    assert result == [12, 13]

    result = [f.id for f in session.execute(Baz.__view__).all()]
    assert result == [1, 2]
