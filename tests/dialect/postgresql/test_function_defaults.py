import pytest
from pytest_mock_resources import PostgresConfig, create_postgres_fixture
from sqlalchemy import text

from sqlalchemy_declarative_extensions import Functions
from sqlalchemy_declarative_extensions.dialects.postgresql import (
    Function,
    FunctionParam,
    FunctionVolatility,
)
from sqlalchemy_declarative_extensions.function.compare import compare_functions

pg = create_postgres_fixture(scope="function", engine_kwargs={"echo": True})




@pytest.mark.parametrize(
    ("default_a", "default_b", "default_c"),
    [(None, None, "''::text"), (1, 0, "'m'::text"), (None, 2, "'ft'::text")],
)
def test_function_argument_defaults(pg, default_a, default_b, default_c):
    add_label_function = Function(
        name="add_label",
        definition="""
            BEGIN
                RETURN (((a + b))::text || c);
            END;
        """,
        parameters=[
            FunctionParam("a", "integer", default=default_a),
            FunctionParam("b", "integer", default=default_b),
            FunctionParam("c", "text", default=default_c),
        ],
        returns="TEXT",
        volatility=FunctionVolatility.STABLE,
        language="plpgsql",
    ).normalize()
    create_function = add_label_function.to_sql_create()
    functions = Functions([add_label_function])
    with pg.connect() as connection:
        connection.execute(text("\n".join(create_function)))
        diff = compare_functions(connection, functions)
    for op in diff:
        assert op.from_function == op.function
