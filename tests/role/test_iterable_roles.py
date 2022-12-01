from pytest_mock_resources import create_postgres_fixture
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_declarative_extensions import (
    declarative_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.dialects import get_roles
from sqlalchemy_declarative_extensions.dialects.postgresql import Role

Base_ = declarative_base()


@declarative_database
class Base(Base_):
    __abstract__ = True

    roles = [
        Role(
            "user",
            superuser=True,
            createdb=True,
            createrole=True,
            inherit=True,
            login=True,
            replication=True,
            bypass_rls=True,
        )
    ]


pg = create_postgres_fixture(scope="function")


register_sqlalchemy_events(Base, roles=True)


def test_createall_role(pg):
    Base.metadata.create_all(bind=pg)

    result = get_roles(pg)
    assert len(result) == 1
    assert result[0].name == "user"
