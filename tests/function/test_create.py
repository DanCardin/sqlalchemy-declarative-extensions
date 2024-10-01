from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, Integer, text

from sqlalchemy_declarative_extensions import (
    Function,
    Functions,
    declarative_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.function.compare import compare_functions
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    functions = Functions().are(
        Function(
            "gimme",
            "INSERT INTO foo (id) VALUES (DEFAULT); SELECT count(*) FROM foo;",
            returns="INTEGER",
        )
    )


class Foo(Base):
    __tablename__ = "foo"

    id = Column(Integer, primary_key=True)


register_sqlalchemy_events(Base.metadata, functions=True)

pg = create_postgres_fixture(engine_kwargs={"echo": True}, session=True)


def test_create(pg):
    Base.metadata.create_all(bind=pg.connection())
    pg.commit()

    result = pg.execute(text("SELECT gimme()")).scalar()
    assert result == 1

    result = pg.execute(text("SELECT gimme()")).scalar()
    assert result == 2

    connection = pg.connection()
    diff = compare_functions(connection, Base.metadata.info["functions"])
    assert diff == []
