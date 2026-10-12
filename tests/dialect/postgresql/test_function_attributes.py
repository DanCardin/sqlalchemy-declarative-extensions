import pytest
from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import text

from sqlalchemy_declarative_extensions import Functions
from sqlalchemy_declarative_extensions.dialects.postgresql import (
    Function,
    FunctionParallel,
    FunctionVolatility,
)
from sqlalchemy_declarative_extensions.function.compare import compare_functions

pg = create_postgres_fixture(scope="function", engine_kwargs={"echo": True})


@pytest.mark.parametrize(
    "attributes",
    [
        {},
        {"parallel": FunctionParallel.restricted},
        {"parallel": FunctionParallel.safe},
        {"strict": True},
        {"leakproof": True},
        {"parallel": FunctionParallel.safe, "strict": True, "leakproof": True},
        # The same attributes, spelled as plain strings.
        {"parallel": "safe"},
        {"volatility": "stable"},
        {"security": "definer"},
        {"parallel": "safe", "strict": True, "leakproof": True},
    ],
)
def test_function_attributes(pg, attributes):
    add_function = Function(
        name="add",
        definition="SELECT a + b;",
        parameters=["a integer", "b integer"],
        returns="INTEGER",
        **attributes,
    ).normalize()
    functions = Functions([add_function])
    with pg.connect() as connection:
        connection.execute(text("\n".join(add_function.to_sql_create())))
        diff = compare_functions(connection, functions)
    assert diff == []


@pytest.mark.parametrize(
    "alias, member",
    [
        (FunctionVolatility.STABLE, FunctionVolatility.stable),
        (FunctionParallel.SAFE, FunctionParallel.safe),
    ],
)
def test_uppercase_alias_is_lowercase_member(alias, member):
    assert alias is member
