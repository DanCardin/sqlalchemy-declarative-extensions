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

    roles = Roles(ignore_unspecified=True).are("read")
    grants = Grants(ignore_unspecified=True).are(
        DefaultGrant.on_tables_in_schema("public").grant("select", to="read")
    )


class Foo(Base):
    __tablename__ = "foo"

    id = Column(types.Integer(), autoincrement=True, primary_key=True)


pg = create_postgres_fixture(scope="function", engine_kwargs={"echo": True})
register_sqlalchemy_events(Base.metadata, schemas=True, roles=True, grants=True)


@pytest.mark.grant
def test_createall_grant(pg):
    pg.execute(text("create role read"))
    pg.execute(text("create table meow (id serial)"))
    pg.execute(text('GRANT INSERT ON TABLE meow to "read"'))
    pg.execute(text('GRANT USAGE ON SEQUENCE meow_id_seq to "read"'))

    Base.metadata.create_all(bind=pg)
    pg.execute(text("commit"))

    # There should be no diffs detected after running `create_all`
    grants = Base.metadata.info["grants"]
    roles = Base.metadata.info["roles"]
    diff = compare_grants(pg, grants, roles)
    assert len(diff) == 0

    # Assert read can only read to foo
    pg.execute(text("SET ROLE read; SELECT * FROM foo"))
    with pytest.raises(sqlalchemy.exc.ProgrammingError):
        pg.execute(text("SET ROLE read; INSERT INTO foo VALUES (DEFAULT)"))

    # Assert read can write to meow. Verifying it was ignored
    pg.execute(text("SET ROLE read; INSERT INTO meow VALUES (DEFAULT)"))
