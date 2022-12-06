import pytest
import sqlalchemy.exc
from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, text, types
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_declarative_extensions import (
    Grants,
    Roles,
    Schemas,
    declarative_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.dialects.postgresql import DefaultGrant, Grant
from sqlalchemy_declarative_extensions.grant.compare import compare_grants

Base_ = declarative_base()


@declarative_database
class Base(Base_):
    __abstract__ = True

    schemas = Schemas().are("bar")
    roles = Roles(ignore_unspecified=True).are("access", "noaccess")
    grants = Grants().are(
        DefaultGrant.on_tables_in_schema("bar").grant("select", to="access"),
        DefaultGrant.on_tables_in_schema("bar").grant("select", to="noaccess"),
        Grant.new("usage", to="access").on_schemas("bar"),
    )


class Bar(Base):
    __tablename__ = "bar"
    __table_args__ = {"schema": "bar"}

    id = Column(types.Integer(), autoincrement=True, primary_key=True)


pg = create_postgres_fixture(scope="function", engine_kwargs={"echo": True})


register_sqlalchemy_events(Base.metadata, schemas=True, roles=True, grants=True)


@pytest.mark.grant
def test_createall_grant(pg):
    Base.metadata.create_all(bind=pg)

    # `access` can access the table because it has usage on the schema
    pg.execute(text("SET ROLE access; SELECT * from bar.bar"))

    # `noaccess` **cannnot** access the table because it does not
    # Assert write can write to foo
    with pytest.raises(sqlalchemy.exc.ProgrammingError):
        pg.execute(text("SET ROLE noaccess; SELECT * FROM foo"))

    grants = Base.metadata.info["grants"]
    roles = Base.metadata.info["roles"]

    # There should be no diffs detected after running `create_all`
    diff = compare_grants(pg, grants, roles)
    assert len(diff) == 0
