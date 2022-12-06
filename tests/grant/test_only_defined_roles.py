import pytest
from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, text, types
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_declarative_extensions import (
    Grants,
    declarative_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.dialects.postgresql import DefaultGrant
from sqlalchemy_declarative_extensions.grant.compare import compare_grants

Base_ = declarative_base()


@declarative_database
class Base(Base_):
    __abstract__ = True

    grants = Grants(only_defined_roles=False, ignore_self_grants=False).are(
        DefaultGrant.on_tables_in_schema("public").grant("select", to="user")
    )


class Foo(Base):
    __tablename__ = "foo"

    id = Column(types.Integer(), autoincrement=True, primary_key=True)


pg = create_postgres_fixture(scope="function", engine_kwargs={"echo": True})
register_sqlalchemy_events(Base.metadata, schemas=True, roles=True, grants=True)


@pytest.mark.grant
def test_createall_grant(pg):
    Base.metadata.create_all(bind=pg)
    pg.execute(text("commit"))

    # There should be no diffs detected after running `create_all`
    grants = Base.metadata.info["grants"]
    roles = Base.metadata.info["roles"]
    diff = compare_grants(pg, grants, roles)
    assert len(diff) == 0

    pg.execute(text("SELECT * FROM foo"))
    pg.execute(text("INSERT INTO foo VALUES (DEFAULT)"))
