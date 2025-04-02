from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, Integer, text

from sqlalchemy_declarative_extensions import Functions, declarative_database, register_sqlalchemy_events
from sqlalchemy_declarative_extensions.dialects.postgresql import Function, FunctionVolatility
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
        ),
        # New function with parameters and volatility
        Function(
            "add_stable",
            "SELECT i + 1;",
            parameters=["i integer"],
            returns="INTEGER",
            volatility=FunctionVolatility.STABLE,
        ),
        # Function returning TABLE
        Function(
            "generate_series_squared",
            '''
            SELECT i, i*i
            FROM generate_series(1, _limit) as i;
            ''',
            language="sql",
            parameters=["_limit integer"],
            returns="TABLE(num integer, num_squared integer)",
            volatility=FunctionVolatility.IMMUTABLE,
        ),
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

    # Test function with parameters
    result_params = pg.execute(text("SELECT add_stable(10)")).scalar()
    assert result_params == 11

    result_params_2 = pg.execute(text("SELECT add_stable(1)")).scalar()
    assert result_params_2 == 2

    # Test function returning table
    result_table = pg.execute(text("SELECT * FROM generate_series_squared(3)")).fetchall()
    assert result_table == [
        (1, 1),
        (2, 4),
        (3, 9),
    ]

    connection = pg.connection()
    diff = compare_functions(connection, Base.metadata.info["functions"])
    assert diff == []
