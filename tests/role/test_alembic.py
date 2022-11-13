import pytest

from tests.utilities import successful_test_run


@pytest.mark.alembic
def test_create_role(pytester):
    successful_test_run(pytester, count=1)


@pytest.mark.alembic
def test_update_role(pytester):
    successful_test_run(pytester, count=1)
