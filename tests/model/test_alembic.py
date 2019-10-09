import pytest

from tests.utilities import successful_test_run


@pytest.mark.alembic
def test_create_models(pytester):
    successful_test_run(pytester, count=1)


@pytest.mark.alembic
def test_update_models(pytester):
    successful_test_run(pytester, count=1)


@pytest.mark.alembic
def test_delete_models(pytester):
    successful_test_run(pytester, count=1)


@pytest.mark.alembic
def test_delete_models_ignore_unspecified(pytester):
    successful_test_run(pytester, count=1)
