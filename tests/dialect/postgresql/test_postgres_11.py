import pytest
from pytest_mock_resources import PostgresConfig, create_postgres_fixture
from sqlalchemy import MetaData, text

from sqlalchemy_declarative_extensions import register_sqlalchemy_events
from sqlalchemy_declarative_extensions.api import declare_database
from sqlalchemy_declarative_extensions.role.base import Roles

metadata = MetaData()
declare_database(metadata, roles=Roles(ignore_unspecified=True))


register_sqlalchemy_events(
    metadata,
    functions=True,
    triggers=True,
    views=True,
    schemas=True,
    roles=True,
    grants=True,
    procedures=True,
)


@pytest.fixture
def pmr_postgres_config():
    return PostgresConfig(port=None, image="postgres:11")


pg = create_postgres_fixture(engine_kwargs={"echo": True}, session=True)


def test_create(pg):
    pg.execute(text("CREATE VIEW foo AS SELECT 1"))
    pg.commit()

    metadata.create_all(bind=pg.connection())
