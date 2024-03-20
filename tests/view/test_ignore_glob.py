from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, text, types

from sqlalchemy_declarative_extensions import (
    Schemas,
    Views,
    declarative_database,
    register_sqlalchemy_events,
    view,
)
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base
from tests import skip_sqlalchemy13

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    schemas = Schemas().are("foo", "bar", "ignoreme")
    views = Views(ignore=["foo.*"], ignore_views=["*.wat"])


@view(Base, register_as_model=True)
class One:
    __tablename__ = "one"
    __table_args__ = {"schema": "bar"}
    __view__ = "SELECT rolname from pg_roles"

    id = Column(types.Integer(), primary_key=True)


register_sqlalchemy_events(Base.metadata, schemas=True, views=True)

pg = create_postgres_fixture(
    scope="function", engine_kwargs={"echo": True}, session=True
)


@skip_sqlalchemy13
def test_ignore_globs(pg):
    pg.execute(text("CREATE SCHEMA foo"))
    pg.execute(text("CREATE SCHEMA ignoreme"))
    pg.execute(text("CREATE VIEW foo.ignoreme AS (SELECT rolname from pg_roles)"))
    pg.execute(text("CREATE VIEW ignoreme.wat AS (SELECT rolname from pg_roles)"))

    Base.metadata.create_all(bind=pg.connection())

    # i.e. these have not been deleted
    pg.execute(text("SELECT * FROM bar.one")).all()
    pg.execute(text("SELECT * FROM foo.ignoreme")).all()
    pg.execute(text("SELECT * FROM ignoreme.wat")).all()
