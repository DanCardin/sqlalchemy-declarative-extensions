from pytest_mock_resources import create_postgres_fixture

from sqlalchemy_declarative_extensions import (
    Schemas,
    declarative_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.dialects.postgresql.schema import schemas_query
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    schemas = Schemas().are("fooschema")


register_sqlalchemy_events(Base.metadata, schemas=True)

pg = create_postgres_fixture(scope="function", engine_kwargs={"echo": True})


def test_createall_schema(pg):
    Base.metadata.create_all(bind=pg)
    with pg.connect() as conn:
        result = conn.execute(schemas_query).fetchall()
    assert result == [("fooschema",)]

    Base.metadata.drop_all(bind=pg)

    with pg.connect() as conn:
        result = conn.execute(schemas_query).fetchall()
    assert result == []
