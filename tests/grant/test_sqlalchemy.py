import pytest
import sqlalchemy.exc
from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, text, types
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_declarative_extensions import (
    declarative_database,
    Grants,
    PGGrant,
    PGRole,
    register_sqlalchemy_events,
    Roles,
)
from sqlalchemy_declarative_extensions.role.compare import get_existing_roles_postgresql

Base_ = declarative_base()


@declarative_database
class Base(Base_):
    __abstract__ = True

    roles = Roles(ignore_unspecified=True).are(
        "read",
        "write",
        PGRole("app", login=False, in_roles=["read", "write"]),
    )
    grants = Grants().are(
        PGGrant("read").grant("select").default().on_tables_in_schema("public"),
        (
            PGGrant("write")
            .grant("insert", "update", "delete")
            .default()
            .on_tables_in_schema("public")
        ),
        PGGrant("write").grant("usage").default().on_sequences_in_schema("public"),
    )


class Foo(Base):
    __tablename__ = "foo"

    id = Column(types.Integer(), autoincrement=True, primary_key=True)


pg = create_postgres_fixture(scope="function", engine_kwargs={"echo": True})


register_sqlalchemy_events(Base.metadata, roles=True, grants=True)


@pytest.mark.grant
def test_createall_grant(pg):
    Base.metadata.create_all(bind=pg)

    roles = get_existing_roles_postgresql(pg, exclude=[pg.pmr_credentials.username])
    result = [role.name for role in roles]

    expected_result = [
        "app",
        "read",
        "write",
    ]
    assert expected_result == result

    # only "write" can write
    with pytest.raises(sqlalchemy.exc.ProgrammingError) as e:
        pg.execute(text("SET ROLE read; INSERT INTO foo VALUES (DEFAULT)"))
    assert "permission denied for relation foo" in str(e.value)

    pg.execute(text("SET ROLE write; INSERT INTO foo VALUES (DEFAULT)"))

    # only "read" can read
    with pytest.raises(sqlalchemy.exc.ProgrammingError) as e:
        pg.execute(text("SET ROLE write; SELECT * FROM foo"))
    assert "permission denied for relation foo" in str(e.value)

    pg.execute(text("SET ROLE read; SELECT * FROM foo"))

    # "app" can do both
    pg.execute(text("SET ROLE app; INSERT INTO foo VALUES (DEFAULT)"))
    pg.execute(text("SET ROLE app; SELECT * FROM foo"))
