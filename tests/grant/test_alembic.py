import pytest

from tests.utilities import successful_test_run


@pytest.mark.grant
@pytest.mark.alembic
def test_identify_grants(pytester):
    successful_test_run(pytester, count=1)


@pytest.mark.grant
@pytest.mark.alembic
def test_grant_update_existing(pytester):
    successful_test_run(pytester, count=1)


@pytest.mark.grant
@pytest.mark.alembic
def test_delete_unspecified_grants(pytester):
    successful_test_run(pytester, count=1)


@pytest.mark.alembic
def test_grant_disabled(pytester):
    successful_test_run(pytester, count=1)
