import pytest
from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import text

from sqlalchemy_declarative_extensions import Grants, Roles
from sqlalchemy_declarative_extensions.dialects.postgresql import DefaultGrant, Grant
from sqlalchemy_declarative_extensions.grant.compare import (
    GrantPrivilegesOp,
    compare_grants,
)

pg = create_postgres_fixture(scope="function", engine_kwargs={"echo": True})


@pytest.mark.grant
def test_createall_grant(pg):
    pg.execute(text("create role test"))
    pg.execute(text("create schema s"))
    pg.execute(text("create table s.foo (id integer)"))
    pg.execute(text("insert into s.foo (id) values (1)"))
    pg.execute(text("insert into s.foo (id) values (11)"))

    pg.execute(text("create view s.vw_foo as (select id from s.foo where id > 10)"))

    pg.execute(text("grant usage on schema s to test"))
    pg.execute(text("grant select on table s.foo to test"))
    pg.execute(
        text("alter default privileges in schema s grant select on tables to test")
    )

    roles = Roles().are("test")
    grants = Grants().are(
        DefaultGrant.on_tables_in_schema("s").grant("select", to="test"),
        Grant.new("usage", to="test").on_schemas("s"),
    )

    diff = compare_grants(pg, grants, roles)
    assert len(diff) == 1
    assert isinstance(diff[0], GrantPrivilegesOp)

    view_grant = str(diff[0].grant.to_sql())
    assert view_grant == 'GRANT SELECT ON TABLE "s"."vw_foo" TO "test";'

    pg.execute(text(view_grant))

    # Assert write can write to foo
    pg.execute(text("SET ROLE test; SELECT * FROM s.vw_foo"))
