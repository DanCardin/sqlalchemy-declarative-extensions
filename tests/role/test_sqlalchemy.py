from datetime import datetime, timezone

from pytest_mock_resources import create_postgres_fixture
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_declarative_extensions import (
    declarative_database,
    register_sqlalchemy_events,
    Roles,
)
from sqlalchemy_declarative_extensions.dialects import get_roles
from sqlalchemy_declarative_extensions.dialects.postgresql import Role

Base_ = declarative_base()


@declarative_database
class Base(Base_):
    __abstract__ = True

    roles = Roles(ignore_unspecified=True).are(
        "nooptions",
        Role(
            "most_options",
            superuser=True,
            createdb=True,
            createrole=True,
            inherit=True,
            login=True,
            replication=True,
            bypass_rls=True,
            connection_limit=1,
            valid_until=datetime(2999, 1, 1),
            in_roles=["nooptions"],
        ),
    )


pg = create_postgres_fixture(scope="function", engine_kwargs={"echo": True})


register_sqlalchemy_events(Base, roles=True)


def test_createall_role(pg):
    Base.metadata.create_all(bind=pg)

    result = get_roles(pg, exclude=[pg.pmr_credentials.username])

    expected_result = [
        Role(
            "most_options",
            superuser=True,
            createdb=True,
            createrole=True,
            login=True,
            replication=True,
            bypass_rls=True,
            connection_limit=1,
            valid_until=datetime(2999, 1, 1, tzinfo=timezone.utc),
            in_roles=["nooptions"],
        ),
        Role(
            "nooptions",
            superuser=False,
            createdb=False,
            createrole=False,
            login=False,
            replication=False,
            bypass_rls=False,
            connection_limit=None,
            valid_until=None,
        ),
    ]
    assert result == expected_result


def test_pg_role_default(pg):
    """Assert a default role with no options matches a default role in postgres."""
    pg.execute("create role foo")
    argumentless_role = get_roles(pg, exclude=[pg.pmr_credentials.username])[0]
    pg.execute("drop role foo")

    pg.execute(Role("foo").to_sql_create())
    default_role = get_roles(pg, exclude=[pg.pmr_credentials.username])[0]

    assert argumentless_role == default_role
