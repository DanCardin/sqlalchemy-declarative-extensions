from datetime import datetime, timezone

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

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
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


register_sqlalchemy_events(Base.metadata, roles=True)


def test_createall_role(pg):
    Base.metadata.create_all(bind=pg)

    with pg.connect() as conn:
        result = get_roles(conn, exclude=[pg.pmr_credentials.username])

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
    with pg.connect() as conn:
        with conn.begin() as trans:
            conn.execute(text("create role foo"))
            argumentless_role = get_roles(conn, exclude=[pg.pmr_credentials.username])[
                0
            ]
            conn.execute(text("drop role foo"))

            for sql in Role("foo").to_sql_create():
                conn.execute(text(sql))
            trans.commit()

        default_role = get_roles(conn, exclude=[pg.pmr_credentials.username])[0]

        assert argumentless_role == default_role
