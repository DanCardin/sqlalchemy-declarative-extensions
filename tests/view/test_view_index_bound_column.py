import pytest
from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, Index, UniqueConstraint, types
from sqlalchemy.dialects.postgresql import dialect as pg_dialect

from sqlalchemy_declarative_extensions import (
    ViewIndex,
    declarative_database,
    register_sqlalchemy_events,
    view,
)
from sqlalchemy_declarative_extensions.dialects.postgresql import View
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True


class Foo(Base):
    __tablename__ = "foo"
    id = Column(types.Integer(), autoincrement=True, primary_key=True)


@view(Base, materialized=True, register_as_model=True)
class Bar:
    __tablename__ = "bar"
    __view__ = "SELECT id FROM foo"
    __table_args__ = (Index("ix_bar_id", "id", unique=True),)

    id = Column(types.Integer(), primary_key=True)


@view(Base, materialized=True, register_as_model=True)
class Baz:
    __tablename__ = "baz"
    __view__ = "SELECT id FROM foo"
    __table_args__ = (UniqueConstraint("id"),)

    id = Column(types.Integer(), primary_key=True)


register_sqlalchemy_events(Base.metadata, views=True)

pg = create_postgres_fixture(scope="function", engine_kwargs={"echo": True})


def test_index_on_register_as_model_view(pg):
    """create_all must not raise TypeError when Index/UniqueConstraint expressions are Column objects."""
    with pg.connect() as conn:
        Base.metadata.create_all(bind=conn)


def test_col_name_raises_for_nameless_column():
    nameless = Column(types.Integer())
    idx = Index("ix_test", nameless)
    v = View("some_view", "SELECT 1", materialized=True)
    with pytest.raises(ValueError, match="has no name"):
        ViewIndex.from_unknown(idx, v, pg_dialect(), None)
