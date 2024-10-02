import pytest

from tests.utilities import successful_test_run


@pytest.mark.alembic
def test_procedure_create(pytester):
    successful_test_run(pytester, count=1)


@pytest.mark.alembic
def test_procedure_rewriter(pytester):
    successful_test_run(pytester, count=1)
