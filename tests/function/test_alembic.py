import pytest

from tests.utilities import successful_test_run


@pytest.mark.alembic
def test_function_create(pytester):
    successful_test_run(pytester, count=1)


@pytest.mark.alembic
def test_function_create_pg_postgis(pytester):
    successful_test_run(pytester, count=1)


@pytest.mark.alembic
def test_function_update(pytester):
    successful_test_run(pytester, count=1)


@pytest.mark.alembic
def test_function_drop(pytester):
    successful_test_run(pytester, count=1)


@pytest.mark.alembic
def test_function_leading_whitespace(pytester):
    successful_test_run(pytester, count=1)


@pytest.mark.alembic
def test_function_rewriter(pytester):
    successful_test_run(pytester, count=1)
