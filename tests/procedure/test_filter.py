from pytest_mock_resources import (
    create_postgres_fixture,
)
from sqlalchemy import text

from sqlalchemy_declarative_extensions import (
    Procedure,
    Schemas,
    declarative_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    schemas = Schemas().are("foo", "bar")
    procedures = [
        Procedure("foo", "select 1"),
        Procedure("bar", "select 1", schema="foo"),
        Procedure("wat", "select 1", schema="bar"),
    ]


register_sqlalchemy_events(Base.metadata, schemas=True, procedures=["public.*", "foo*"])

pg = create_postgres_fixture(
    scope="function", engine_kwargs={"echo": True}, session=True
)


def test_filter(pg):
    Base.metadata.create_all(bind=pg.connection())

    result = pg.execute(
        text(
            "SELECT n.nspname, proname FROM pg_proc JOIN pg_namespace n ON pg_proc.pronamespace = n.oid "
            "where n.nspname not like 'inform%' and n.nspname not like 'pg%'"
        )
    ).fetchall()

    assert sorted(result) == [("foo", "bar"), ("public", "foo")]
