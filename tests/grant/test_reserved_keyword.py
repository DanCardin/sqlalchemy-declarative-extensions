import pytest
from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, text, types

from sqlalchemy_declarative_extensions import (
    Grants,
    Roles,
    Schemas,
    declarative_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.dialects.postgresql import DefaultGrant, Grant
from sqlalchemy_declarative_extensions.grant.compare import compare_grants
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    schemas = Schemas().are("null")
    roles = Roles(ignore_unspecified=True).are("app")
    grants = Grants().are(
        Grant.new("usage", to="app").on_schemas("null"),
        DefaultGrant.on_tables_in_schema("null").grant("select", to="app"),
    )


class Foo(Base):
    __tablename__ = "foo"
    __table_args__ = {"schema": "null"}

    id = Column(types.Integer(), autoincrement=True, primary_key=True)


pg = create_postgres_fixture(scope="function", engine_kwargs={"echo": True})


register_sqlalchemy_events(Base.metadata, schemas=True, roles=True, grants=True)


@pytest.mark.grant
def test_createall_grant(pg):
    Base.metadata.create_all(bind=pg)

    # There should be no diffs detected after running `create_all`
    grants = Base.metadata.info["grants"]
    roles = Base.metadata.info["roles"]
    with pg.connect() as conn:
        diff = compare_grants(conn, grants, roles)
    assert len(diff) == 0

    with pg.connect() as conn:
        conn.execute(text("""SET ROLE app; SELECT * FROM "null"."foo";"""))
