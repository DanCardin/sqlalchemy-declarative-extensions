import pytest

from tests.utilities import successful_test_run


@pytest.mark.alembic
def test_schema_disabled(pytester):
    successful_test_run(pytester, count=1)


@pytest.mark.alembic
def test_schema_create(pytester):
    successful_test_run(pytester, count=1)


@pytest.mark.alembic
def test_schema_rewriter(pytester):
    successful_test_run(pytester, count=1)


@pytest.mark.alembic
def test_schema_drop(pytester):
    successful_test_run(pytester, count=1)


@pytest.mark.alembic
def test_schema_ignore_unspecified(pytester):
    successful_test_run(pytester, count=1)
