import pytest

from tests.utilities import successful_test_run


@pytest.mark.alembic
def test_trigger_create(pytester):
    successful_test_run(pytester, count=1)


@pytest.mark.alembic
def test_trigger_update(pytester):
    successful_test_run(pytester, count=1)


@pytest.mark.alembic
def test_trigger_drop(pytester):
    successful_test_run(pytester, count=1)


@pytest.mark.alembic
def test_trigger_rewriter(pytester):
    successful_test_run(pytester, count=1)
