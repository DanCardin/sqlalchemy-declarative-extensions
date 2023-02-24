import pytest

from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import text

from sqlalchemy_declarative_extensions import (
    Roles,
    declarative_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.dialects import get_roles
from sqlalchemy_declarative_extensions.dialects.postgresql import Role
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

Base_ = declarative_base()


@declarative_database
class Base(Base_):
    __abstract__ = True

    roles = Roles(ignore_unspecified=True).are(
        Role("forever_valid", valid_until=None),
    )


pg = create_postgres_fixture(scope="function", engine_kwargs={"echo": True})


register_sqlalchemy_events(Base, roles=True)


@pytest.mark.parametrize("valid_until", ("2020-01-01", "infinity"))
def test_valid_until_infinity(pg, valid_until):
    with pg.connect() as conn:
        conn.execute(text("CREATE ROLE forever_valid WITH PASSWORD 'p';"))
        conn.execute(text(f"ALTER ROLE forever_valid VALID UNTIL '{valid_until}'"))

    Base.metadata.create_all(bind=pg)

    with pg.connect() as conn:
        result = get_roles(conn, exclude=[pg.pmr_credentials.username])

    expected_result = [Role("forever_valid")]
    assert result == expected_result
