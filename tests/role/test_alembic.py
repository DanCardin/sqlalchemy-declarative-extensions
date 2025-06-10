import pytest

from tests.utilities import successful_test_run


@pytest.mark.alembic
def test_create_role(pytester):
    successful_test_run(pytester, count=2)


@pytest.mark.alembic
def test_update_role(pytester):
    successful_test_run(pytester, count=1)


@pytest.mark.alembic
def test_role_disabled(pytester):
    successful_test_run(pytester, count=1)


@pytest.mark.alembic
def test_role_operations(pytester):
    successful_test_run(pytester, count=1)


@pytest.mark.alembic
def test_role_rewriter(pytester):
    successful_test_run(pytester, count=1)
