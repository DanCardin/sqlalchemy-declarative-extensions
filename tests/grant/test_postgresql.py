import pytest

from sqlalchemy_declarative_extensions.grant.postgresql import for_role
from sqlalchemy_declarative_extensions.role.base import Role
from tests.utilities import render_sql


class Test_for_role:
    @pytest.mark.parametrize("role", ("foo", Role("foo")))
    def test_basic_grant(self, role):
        grant = for_role(role).grant("select").on_table("bar")
        sql = render_sql(grant.to_sql())

        expected_result = "GRANT SELECT ON TABLE bar TO foo"
        assert expected_result == sql

    def test_basic_revoke(self):
        grant = for_role("foo").revoke("select").on_table("bar")
        sql = render_sql(grant.to_sql())

        expected_result = "REVOKE SELECT ON TABLE bar FROM foo"
        assert expected_result == sql

    def test_with_grant_options(self):
        grant = for_role("foo").grant("select").with_grant_option().on_table("bar")
        sql = render_sql(grant.to_sql())

        expected_result = "GRANT SELECT ON TABLE bar TO foo WITH GRANT OPTION"
        assert expected_result == sql

    def test_on_multiple_tables(self):
        grant = for_role("foo").grant("select").on_table("bar", "baz")
        sql = render_sql(grant.to_sql())

        expected_result = "GRANT SELECT ON TABLE bar, baz TO foo"
        assert expected_result == sql

    def test_on_schemas(self):
        grant = for_role("foo").grant("usage").in_schema("bar", "meow")
        sql = render_sql(grant.to_sql())

        expected_result = "GRANT USAGE ON SCHEMA bar, meow TO foo"
        assert expected_result == sql


class Test_for_role_default:
    def test_on_tables(self):
        grant = (
            for_role("foo").grant("select").default().on_tables_in_schema("bar", "baz")
        )
        sql = render_sql(grant.to_sql())

        expected_result = (
            "ALTER DEFAULT PRIVILEGES IN SCHEMA bar, baz "
            "GRANT SELECT ON TABLES TO foo"
        )
        assert expected_result == sql

    def test_for_role(self):
        grant = (
            for_role("foo")
            .grant("select")
            .default()
            .on_tables_in_schema("bar", "baz", for_role="test")
        )
        sql = render_sql(grant.to_sql())

        expected_result = (
            "ALTER DEFAULT PRIVILEGES FOR ROLE test IN SCHEMA bar, baz "
            "GRANT SELECT ON TABLES TO foo"
        )
        assert expected_result == sql

    def test_on_sequences(self):
        grant = for_role("foo").grant("select").default().on_sequences_in_schema("bar")
        sql = render_sql(grant.to_sql())

        expected_result = (
            "ALTER DEFAULT PRIVILEGES IN SCHEMA bar GRANT SELECT ON SEQUENCES TO foo"
        )
        assert expected_result == sql

    def test_on_functions(self):
        grant = for_role("foo").grant("execute").default().on_functions_in_schema("bar")
        sql = render_sql(grant.to_sql())

        expected_result = (
            "ALTER DEFAULT PRIVILEGES IN SCHEMA bar "
            "GRANT EXECUTE ON FUNCTIONS TO foo"
        )
        assert expected_result == sql

    def test_on_types(self):
        grant = for_role("foo").grant("USAGE").default().on_types_in_schema("bar")
        sql = render_sql(grant.to_sql())

        expected_result = (
            "ALTER DEFAULT PRIVILEGES IN SCHEMA bar GRANT USAGE ON TYPES TO foo"
        )
        assert expected_result == sql
