import pytest
import sqlalchemy.exc
from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, text, types

from sqlalchemy_declarative_extensions import (
    Roles,
    declarative_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    roles = Roles(ignore_unspecified=True).are("write")


class Foo(Base):
    __tablename__ = "foo"

    id = Column(types.Integer(), autoincrement=True, primary_key=True)


pg = create_postgres_fixture(scope="function", engine_kwargs={"echo": True})


register_sqlalchemy_events(Base.metadata, schemas=True, roles=True, grants=True)


@pytest.mark.grant
def test_createall_grant(pg):
    with pg.connect() as conn:
        with conn.begin() as trans:
            conn.execute(text("create table meow (id serial)"))
            trans.commit()

    Base.metadata.create_all(bind=pg)
    with pg.connect() as conn:
        conn.execute(text("commit"))

    with pytest.raises(sqlalchemy.exc.ProgrammingError):
        with pg.connect() as conn:
            conn.execute(text("SET ROLE write; INSERT INTO meow VALUES (DEFAULT)"))
