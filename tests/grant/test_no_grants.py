import pytest
import sqlalchemy.exc
from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, text, types
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_declarative_extensions import (
    Roles,
    declarative_database,
    register_sqlalchemy_events,
)

Base_ = declarative_base()


@declarative_database
class Base(Base_):
    __abstract__ = True

    roles = Roles(ignore_unspecified=True).are("write")


class Foo(Base):
    __tablename__ = "foo"

    id = Column(types.Integer(), autoincrement=True, primary_key=True)


pg = create_postgres_fixture(scope="function", engine_kwargs={"echo": True})


register_sqlalchemy_events(Base.metadata, schemas=True, roles=True, grants=True)


@pytest.mark.grant
def test_createall_grant(pg):
    pg.execute(text("create table meow (id serial)"))

    Base.metadata.create_all(bind=pg)
    pg.execute(text("commit"))

    with pytest.raises(sqlalchemy.exc.ProgrammingError):
        pg.execute(text("SET ROLE write; INSERT INTO meow VALUES (DEFAULT)"))
