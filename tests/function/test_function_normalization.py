from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import text

from sqlalchemy_declarative_extensions import (
    declarative_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.function.compare import (
    DropFunctionOp,
    compare_functions,
)
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    functions: list = []


register_sqlalchemy_events(Base.metadata, functions=True)

pg = create_postgres_fixture(engine_kwargs={"echo": True}, session=True)


def test_existing_function_normalized(pg):
    Base.metadata.create_all(bind=pg.connection())
    pg.commit()

    pg.execute(
        text(
            """
    CREATE OR REPLACE FUNCTION echo_any_element(
        input_value ANYELEMENT
    )
    RETURNS ANYELEMENT
    LANGUAGE sql
    AS $$
        -- A generic function using the ANYELEMENT polymorphic type
        SELECT input_value;
    $$;
    """
        )
    )

    connection = pg.connection()
    diff = compare_functions(connection, Base.metadata.info["functions"])

    assert len(diff) == 1
    assert isinstance(diff[0], DropFunctionOp)
    assert "DROP FUNCTION" in diff[0].to_sql()[0]
    assert "CREATE FUNCTION" in diff[0].reverse().to_sql()[0]
