from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, text, types

from sqlalchemy_declarative_extensions import (
    Functions,
    declarative_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.function.base import Procedure
from sqlalchemy_declarative_extensions.function.compare import compare_functions
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    functions = Functions().are(Procedure("gimme", "INSERT INTO foo VALUES (DEFAULT);"))


class Foo(Base):
    __tablename__ = "foo"

    id = Column(types.Integer(), primary_key=True, autoincrement=True)


register_sqlalchemy_events(Base.metadata, functions=True)

pg = create_postgres_fixture(engine_kwargs={"echo": True}, session=True)


def test_create(pg):
    Base.metadata.create_all(bind=pg.connection())
    pg.commit()

    result = pg.execute(text("CALL gimme()"))
    result = pg.execute(text("CALL gimme()"))
    result = pg.query(Foo).count()
    assert result == 2

    connection = pg.connection()
    diff = compare_functions(connection, Base.metadata.info["functions"], Base.metadata)
    assert diff == []
