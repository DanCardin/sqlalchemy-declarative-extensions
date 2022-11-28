import pytest
import sqlalchemy.exc
from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, text, types
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_declarative_extensions import (
    declarative_database,
    Grants,
    register_sqlalchemy_events,
    Roles,
)
from sqlalchemy_declarative_extensions.dialects.postgresql import DefaultGrant
from sqlalchemy_declarative_extensions.grant.compare import compare_grants

Base_ = declarative_base()


@declarative_database
class Base(Base_):
    __abstract__ = True

    roles = Roles(ignore_unspecified=True).are("foo")
    grants = Grants(default_grants_imply_grants=False).are(
        DefaultGrant.on_tables_in_schema("public").grant("select", "insert", to="foo"),
    )


class Foo(Base):
    __tablename__ = "foo"

    id = Column(types.Integer(), autoincrement=True, primary_key=True)


pg = create_postgres_fixture(scope="function", engine_kwargs={"echo": True})
register_sqlalchemy_events(Base.metadata, schemas=True, roles=True, grants=True)


@pytest.mark.grant
def test_createall_grant(pg):
    pg.execute(text("create role foo"))
    pg.execute(text("create table bar (id integer)"))

    Base.metadata.create_all(bind=pg)

    # There should be no diffs detected after running `create_all`
    grants = Base.metadata.info["grants"]
    roles = Base.metadata.info["roles"]
    diff = compare_grants(pg, grants, roles)
    assert len(diff) == 0

    pg.execute(text("set role foo; SELECT * FROM foo"))
    pg.execute(text("set role foo; INSERT INTO foo VALUES (1)"))

    with pytest.raises(sqlalchemy.exc.ProgrammingError):
        pg.execute(text("set role foo; SELECT * FROM bar"))

    with pytest.raises(sqlalchemy.exc.ProgrammingError):
        pg.execute(text("set role foo; INSERT INTO bar VALUES (1)"))
