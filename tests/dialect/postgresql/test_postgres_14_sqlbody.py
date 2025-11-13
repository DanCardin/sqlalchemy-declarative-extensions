import pytest
from pytest_mock_resources import PostgresConfig, create_postgres_fixture
from sqlalchemy import text

from sqlalchemy_declarative_extensions import Functions
from sqlalchemy_declarative_extensions.dialects.postgresql import (
    Function,
    FunctionVolatility,
)
from sqlalchemy_declarative_extensions.function.compare import compare_functions

pg = create_postgres_fixture(scope="function", engine_kwargs={"echo": True})


@pytest.fixture
def pmr_postgres_config():
    return PostgresConfig(image="postgres:14", port=None, ci_port=None)


def test_functions(pg):
    add_stable_function = Function(
        name="add_stable",
        definition="RETURN (i + 1)",
        parameters=["i integer"],
        returns="INTEGER",
        volatility=FunctionVolatility.STABLE,
    ).normalize()
    create_function = add_stable_function.to_sql_create()
    functions = Functions([add_stable_function])
    with pg.connect() as connection:
        connection.execute(text("\n".join(create_function)))
        diff = compare_functions(connection, functions)
    for op in diff:
        assert op.from_function == op.function
