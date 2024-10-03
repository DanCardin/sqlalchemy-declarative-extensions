import pytest

from tests.utilities import successful_test_run


@pytest.mark.alembic
def test_view_create_pg(pytester):
    successful_test_run(pytester, count=1)


@pytest.mark.alembic
@pytest.mark.mysql
def test_view_create_mysql(pytester):
    successful_test_run(pytester, count=1)


@pytest.mark.alembic
def test_view_drop_pg(pytester):
    successful_test_run(pytester, count=1)


@pytest.mark.alembic
@pytest.mark.mysql
def test_view_drop_mysql(pytester):
    successful_test_run(pytester, count=1)


@pytest.mark.alembic
def test_view_update_pg(pytester):
    successful_test_run(pytester, count=1)


@pytest.mark.alembic
@pytest.mark.mysql
def test_view_update_mysql(pytester):
    successful_test_run(pytester, count=1)


@pytest.mark.alembic
def test_view_materialized_constraint(pytester):
    successful_test_run(pytester, count=1)


@pytest.mark.alembic
def test_view_complex_comparison_pg(pytester):
    successful_test_run(pytester, count=1)


@pytest.mark.alembic
def test_view_rewriter(pytester):
    successful_test_run(pytester, count=1)
