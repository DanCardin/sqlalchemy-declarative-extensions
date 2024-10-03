from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, text, types

from sqlalchemy_declarative_extensions import (
    Schemas,
    Views,
    declarative_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base
from sqlalchemy_declarative_extensions.view.compare import compare_views

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    schemas = Schemas().are("fooschema")
    views = Views(ignore_unspecified=True)


class Foo(Base):
    __tablename__ = "foo"
    __table_args__ = {"schema": "fooschema"}

    id = Column(types.Integer(), primary_key=True)


register_sqlalchemy_events(Base.metadata, schemas=True, views=True, rows=True)

pg = create_postgres_fixture(
    scope="function", engine_kwargs={"echo": True}, session=True
)


def test_ignore_views(pg):
    Base.metadata.create_all(bind=pg.connection())

    pg.execute(text("CREATE VIEW meow as (SELECT id from fooschema.foo)"))

    # Verify this no longer sees changes to make! Failing here would imply the autogenerate
    # is not fully normalizing the difference.
    result = compare_views(pg.connection(), views=Base.views)
    assert result == []
