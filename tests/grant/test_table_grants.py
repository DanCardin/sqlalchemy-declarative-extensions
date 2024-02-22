import pytest
import sqlalchemy.exc
from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, text, types

from sqlalchemy_declarative_extensions import (
    Grants,
    Roles,
    Schemas,
    declarative_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.dialects.postgresql import DefaultGrant, Role
from sqlalchemy_declarative_extensions.grant.compare import compare_grants
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    schemas = Schemas().are("bar")
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
        DefaultGrant.on_sequences_in_schema("public").grant(
            "usage", "select", to="write"
        ),
    )


class Foo(Base):
    __tablename__ = "foo"

    id = Column(types.Integer(), autoincrement=True, primary_key=True)


class Bar(Base):
    __tablename__ = "bar"
    __table_args__ = {"schema": "bar"}

    id = Column(types.Integer(), autoincrement=True, primary_key=True)


pg = create_postgres_fixture(scope="function", engine_kwargs={"echo": True})


register_sqlalchemy_events(Base.metadata, schemas=True, roles=True, grants=True)


@pytest.mark.grant
def test_createall_grant(pg):
    with pg.connect() as conn:
        with conn.begin() as trans:
            conn.execute(text("create table meow (id serial)"))
            trans.commit()

    Base.metadata.create_all(bind=pg)

    with pg.connect() as conn:
        # Assert write can write to foo
        conn.execute(text("SET ROLE write; INSERT INTO foo VALUES (DEFAULT)"))

        # Assert write can write to foo
        conn.execute(text("SET ROLE read; SELECT * FROM foo"))

        grants = Base.metadata.info["grants"]
        roles = Base.metadata.info["roles"]

        # There should be no diffs detected after running `create_all`
        diff = compare_grants(conn, grants, roles)
        assert len(diff) == 0

        # Assert write can write to meow, despite the fact that it was created before
        # the default grants
        conn.execute(text("SET ROLE write; INSERT INTO meow VALUES (DEFAULT)"))

        # Assert write can read from meow, despite the fact that it was created before
        # the default grants
        conn.execute(text("SET ROLE read; SELECT * FROM meow"))

    # We shouldn't have applied anything to bar.bar
    with pytest.raises(sqlalchemy.exc.ProgrammingError):
        with pg.connect() as conn:
            conn.execute(text("SET ROLE write; INSERT INTO bar.bar VALUES (DEFAULT)"))

    with pytest.raises(sqlalchemy.exc.ProgrammingError):
        with pg.connect() as conn:
            conn.execute(text("SET ROLE read; SELECT * FROM bar.bar"))
