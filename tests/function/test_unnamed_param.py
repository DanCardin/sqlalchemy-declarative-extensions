from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import text

from sqlalchemy_declarative_extensions.dialects.postgresql.function import Function
from sqlalchemy_declarative_extensions.function.base import Functions
from sqlalchemy_declarative_extensions.function.compare import (
    DropFunctionOp,
    compare_functions,
)

pg = create_postgres_fixture(engine_kwargs={"echo": True}, session=True)


def test_existing_function(pg):
    pg.execute(
        text(
            """
            CREATE OR REPLACE FUNCTION add_numbers(integer, integer)
            RETURNS integer AS $$
            BEGIN
                RETURN $1 + $2;
            END;
            $$ LANGUAGE plpgsql;
            """
        )
    )

    connection = pg.connection()
    diff = compare_functions(connection, Functions())

    assert len(diff) == 1
    assert isinstance(diff[0], DropFunctionOp)
    assert "DROP FUNCTION" in diff[0].to_sql()[0]
    assert "CREATE FUNCTION" in diff[0].reverse().to_sql()[0]


def test_creates_function(pg):
    connection = pg.connection()
    diff = compare_functions(
        connection,
        Functions(
            functions=[
                Function(
                    "add_numbers",
                    """
                    BEGIN
                        RETURN $1 + $2;
                    END;
                    """,
                    language="plpgsql",
                    returns="integer",
                    parameters=["integer", "integer"],
                )
            ]
        ),
    )

    assert len(diff) == 1
    assert "CREATE FUNCTION" in diff[0].to_sql()[0]
    pg.execute(text(diff[0].to_sql()[0]))
    pg.commit()

    result = pg.execute(text("SELECT add_numbers(2, 3)")).one()[0]
    assert result == 5
