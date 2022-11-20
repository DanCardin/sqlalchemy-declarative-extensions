import pytest

from tests.utilities import successful_test_run


@pytest.mark.alembic
def test_schema_disabled(pytester):
    successful_test_run(pytester, count=1)
