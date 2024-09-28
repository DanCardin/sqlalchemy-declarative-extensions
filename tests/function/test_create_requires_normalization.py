from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, text, types

from sqlalchemy_declarative_extensions import (
    Function,
    declarative_database,
    register_function,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.function.compare import compare_functions
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True


function = Function(
    "gimme",
    """
            BEGIN
            INSERT INTO foo (id)
            SELECT 1;
            RETURN NULL;
            END
            """,
    returns="INTEGER",
    language="plpgsql",
)
register_function(Base.metadata, function)


class Foo(Base):
    __tablename__ = "foo"

    id = Column(types.Integer(), primary_key=True)


register_sqlalchemy_events(Base.metadata, functions=True)

pg = create_postgres_fixture(engine_kwargs={"echo": True}, session=True)


def test_create_with_complex_function_requiring_normalization(pg):
    Base.metadata.create_all(bind=pg.connection())
    pg.commit()

    result = pg.execute(text("SELECT gimme()")).scalar()
    assert result is None

    result = pg.query(Foo.id).scalar()
    assert result == 1

    connection = pg.connection()
    diff = compare_functions(connection, Base.metadata.info["functions"])
    assert diff == []
