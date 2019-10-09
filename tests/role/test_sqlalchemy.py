from datetime import datetime, timezone

from pytest_mock_resources import create_postgres_fixture
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_declarative_extensions import declarative_database, PGRole, Roles
from sqlalchemy_declarative_extensions.role.compare import get_existing_roles_postgresql

Base_ = declarative_base()


@declarative_database
class Base(Base_):
    __abstract__ = True

    roles = Roles().are(
        "nooptions",
        PGRole(
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


pg = create_postgres_fixture()


def test_createall_role(pg):
    Base.metadata.create_all(bind=pg)

    result = get_existing_roles_postgresql(pg, exclude=[pg.pmr_credentials.username])

    expected_result = [
        PGRole(
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
        PGRole(
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
