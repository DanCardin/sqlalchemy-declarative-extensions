import pytest
from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, types
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_declarative_extensions import (
    declarative_database,
    register_sqlalchemy_events,
    Row,
    Rows,
)

Base_ = declarative_base()


@declarative_database
class Base(Base_):
    __abstract__ = True

    rows = Rows(ignore_unspecified=True).are(
        Row("foo.foo", name="qwer"),
    )


class Foo(Base):
    __tablename__ = "foo"

    id = Column(types.Integer(), primary_key=True)
    name = Column(types.Unicode(), nullable=False)


register_sqlalchemy_events(Base.metadata, rows=True)

pg = create_postgres_fixture(
    scope="function", engine_kwargs={"echo": True}, session=True
)


def test_insert_missing(pg):
    with pytest.raises(ValueError):
        Base.metadata.create_all(bind=pg.connection())
