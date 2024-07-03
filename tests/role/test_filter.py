from pytest_mock_resources import create_postgres_fixture

from sqlalchemy_declarative_extensions import (
    Roles,
    declarative_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.dialects import get_roles
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    roles = Roles(ignore_unspecified=True).are("foo", "foobar", "meow")


pg = create_postgres_fixture(scope="function", engine_kwargs={"echo": True})


register_sqlalchemy_events(Base.metadata, roles=["foo*"])


def test_createall_role(pg):
    Base.metadata.create_all(bind=pg)

    with pg.connect() as conn:
        result = get_roles(conn, exclude=[pg.pmr_credentials.username])

    result = [role.name for role in result]
    expected_result = ["foo", "foobar"]
    assert result == expected_result
