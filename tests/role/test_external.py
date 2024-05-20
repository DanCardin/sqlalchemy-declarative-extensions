import pytest
import sqlalchemy.exc
from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import MetaData, text

from sqlalchemy_declarative_extensions import Roles
from sqlalchemy_declarative_extensions.api import (
    declare_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.dialects.postgresql import Role
from sqlalchemy_declarative_extensions.role.compare import CreateRoleOp, compare_roles

pg = create_postgres_fixture(scope="function")


def test_no_attempt_to_create(pg):
    external = Role("external", external=True)
    roles = Roles(ignore_unspecified=True).are(external)

    metadata = MetaData()
    declare_database(metadata, roles=roles)
    register_sqlalchemy_events(metadata, roles=True)

    with pg.connect() as conn:
        ops = compare_roles(conn, roles)

    assert ops == []


def test_no_attempt_to_create_thus_error(pg):
    external = Role("external", external=True)
    new_role = Role("new_role", in_roles=[external])
    roles = Roles(ignore_unspecified=True).are(external, new_role)

    metadata = MetaData()
    declare_database(metadata, roles=roles)
    register_sqlalchemy_events(metadata, roles=True)

    with pg.connect() as conn:
        ops = compare_roles(conn, roles)

    assert ops == [
        CreateRoleOp(role=Role(name="new_role", in_roles=["external"])),
    ]

    with pytest.raises(sqlalchemy.exc.ProgrammingError) as e:
        metadata.create_all(bind=pg)

    assert 'role "external" does not exist' in str(e)


def test_works_when_exists(pg):
    external = Role("external", external=True)
    new_role = Role("new_role", in_roles=[external])
    roles = Roles(ignore_unspecified=True).are(external, new_role)

    metadata = MetaData()
    declare_database(metadata, roles=roles)
    register_sqlalchemy_events(metadata, roles=True)

    with pg.begin() as conn:
        conn.execute(text("CREATE ROLE external"))

    with pg.connect() as conn:
        ops = compare_roles(conn, roles)

    assert ops == [
        CreateRoleOp(role=Role(name="new_role", in_roles=["external"])),
    ]

    metadata.create_all(bind=pg)

    with pg.connect() as conn:
        ops = compare_roles(conn, roles)
    assert ops == []
