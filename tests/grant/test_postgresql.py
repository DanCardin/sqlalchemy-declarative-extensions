import pytest

from sqlalchemy_declarative_extensions import Role
from sqlalchemy_declarative_extensions.dialects.postgresql import (
    DefaultGrant,
    Grant,
    TableGrants,
)
from tests.utilities import render_sql


class TestGrant:
    @pytest.mark.parametrize("role", ("foo", Role("foo")))
    def test_basic_grant(self, role):
        grant = Grant.new("select", to=role).on_tables("bar")
        sql = render_sql(grant.to_sql())

        expected_result = 'GRANT SELECT ON TABLE "bar" TO "foo";'
        assert expected_result == sql

    def test_basic_revoke(self):
        grant = Grant.new("select", to="foo").revoke().on_tables("bar")
        sql = render_sql(grant.to_sql())

        expected_result = 'REVOKE SELECT ON TABLE "bar" FROM "foo";'
        assert expected_result == sql

    def test_with_grant_options(self):
        grant = Grant.new("select", to="foo").with_grant_option().on_tables("bar")
        sql = render_sql(grant.to_sql())

        expected_result = 'GRANT SELECT ON TABLE "bar" TO "foo" WITH GRANT OPTION;'
        assert expected_result == sql

    def test_on_multiple_tables(self):
        grant = Grant.new("select", to="foo").on_tables("bar", "baz")
        sql = render_sql(grant.to_sql())

        expected_result = 'GRANT SELECT ON TABLE "bar", "baz" TO "foo";'
        assert expected_result == sql

    def test_on_schemas(self):
        grant = Grant.new("usage", to="foo").on_schemas("bar", "meow")
        sql = render_sql(grant.to_sql())

        expected_result = 'GRANT USAGE ON SCHEMA "bar", "meow" TO "foo";'
        assert expected_result == sql


class TestGrantDefault:
    def test_on_tables(self):
        grant = DefaultGrant.on_tables_in_schema("bar", "baz").grant("select", to="foo")
        sql = render_sql(grant.to_sql())

        expected_result = (
            'ALTER DEFAULT PRIVILEGES IN SCHEMA "bar", "baz" '
            'GRANT SELECT ON TABLES TO "foo";'
        )
        assert expected_result == sql

    def test_grant_type_object(self):
        grant = (
            DefaultGrant.on_tables_in_schema("bar", "baz")
            .for_role("test")
            .grant(TableGrants.select, to="foo")
        )
        sql = render_sql(grant.to_sql())

        expected_result = (
            'ALTER DEFAULT PRIVILEGES FOR ROLE "test" IN SCHEMA "bar", "baz" '
            'GRANT SELECT ON TABLES TO "foo";'
        )
        assert expected_result == sql

    def test_on_sequences(self):
        grant = DefaultGrant.on_sequences_in_schema("bar").grant("select", to="foo")
        sql = render_sql(grant.to_sql())

        expected_result = 'ALTER DEFAULT PRIVILEGES IN SCHEMA "bar" GRANT SELECT ON SEQUENCES TO "foo";'
        assert expected_result == sql

    def test_on_functions(self):
        grant = DefaultGrant.on_functions_in_schema("bar").grant("execute", to="foo")
        sql = render_sql(grant.to_sql())

        expected_result = (
            'ALTER DEFAULT PRIVILEGES IN SCHEMA "bar" '
            'GRANT EXECUTE ON FUNCTIONS TO "foo";'
        )
        assert expected_result == sql

    def test_on_types(self):
        grant = DefaultGrant.on_types_in_schema("bar").grant("usage", to="foo")
        sql = render_sql(grant.to_sql())

        expected_result = (
            'ALTER DEFAULT PRIVILEGES IN SCHEMA "bar" GRANT USAGE ON TYPES TO "foo";'
        )
        assert expected_result == sql
