import pytest
import sqlalchemy.exc
from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import MetaData

from sqlalchemy_declarative_extensions import Roles
from sqlalchemy_declarative_extensions.api import (
    declare_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.dialects.postgresql import Role
from sqlalchemy_declarative_extensions.role.compare import CreateRoleOp, compare_roles

pg = create_postgres_fixture(scope="function")


def test_no_attempt_to_create(pg):
    used = Role("used", createrole=False)

    with used:
        will_fail = Role("will_fail")

    roles = Roles(ignore_unspecified=True).are(used, will_fail)

    metadata = MetaData()
    declare_database(metadata, roles=roles)
    register_sqlalchemy_events(metadata, roles=True)

    with pg.connect() as conn:
        ops = compare_roles(conn, roles)

    assert len(ops) == 2
    assert isinstance(ops[1], CreateRoleOp)
    assert ops[1].role.use_role == "used"

    with pytest.raises(sqlalchemy.exc.ProgrammingError) as e:
        metadata.create_all(bind=pg)
    assert "permission denied to create role" in str(e)
