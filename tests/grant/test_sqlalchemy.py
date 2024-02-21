import pytest
import sqlalchemy.exc
from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, text, types

from sqlalchemy_declarative_extensions import (
    Grants,
    Roles,
    declarative_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.dialects import get_roles
from sqlalchemy_declarative_extensions.dialects.postgresql import DefaultGrant, Role
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    roles = Roles(ignore_unspecified=True).are(
        "read",
        "write",
        Role("app", login=False, in_roles=["read", "write"]),
    )
    grants = Grants().are(
        DefaultGrant.on_tables_in_schema("public").grant("select", to="read"),
        DefaultGrant.on_tables_in_schema("public").grant(
            "insert", "update", "delete", to="write"
        ),
        DefaultGrant.on_sequences_in_schema("public").grant("usage", to="write"),
    )


class Foo(Base):
    __tablename__ = "foo"

    id = Column(types.Integer(), autoincrement=True, primary_key=True)


pg = create_postgres_fixture(scope="function", engine_kwargs={"echo": True})


register_sqlalchemy_events(Base.metadata, roles=True, grants=True)


@pytest.mark.grant
def test_createall_grant(pg):
    Base.metadata.create_all(bind=pg)

    with pg.connect() as conn:
        roles = get_roles(conn, exclude=[pg.pmr_credentials.username])
    result = [role.name for role in roles]

    expected_result = [
        "app",
        "read",
        "write",
    ]
    assert expected_result == result

    # only "write" can write
    with pytest.raises(sqlalchemy.exc.ProgrammingError) as e:
        with pg.connect() as conn:
            conn.execute(text("SET ROLE read; INSERT INTO foo VALUES (DEFAULT)"))
    assert "permission denied for relation foo" in str(e.value).replace(
        "table", "relation"
    )

    with pg.connect() as conn:
        conn.execute(text("SET ROLE write; INSERT INTO foo VALUES (DEFAULT)"))

    # only "read" can read
    with pytest.raises(sqlalchemy.exc.ProgrammingError) as e:
        with pg.connect() as conn:
            conn.execute(text("SET ROLE write; SELECT * FROM foo"))
    assert "permission denied for relation foo" in str(e.value).replace(
        "table", "relation"
    )

    with pg.connect() as conn:
        conn.execute(text("SET ROLE read; SELECT * FROM foo"))

        # "app" can do both
        conn.execute(text("SET ROLE app; INSERT INTO foo VALUES (DEFAULT)"))
        conn.execute(text("SET ROLE app; SELECT * FROM foo"))
