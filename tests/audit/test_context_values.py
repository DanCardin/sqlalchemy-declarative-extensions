import pytest
import sqlalchemy.exc
from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, types
from sqlalchemy.dialects.postgresql import JSONB

from sqlalchemy_declarative_extensions import (
    declarative_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.audit import audit, set_context_values
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore  # type: ignore
    __abstract__ = True


context_columns = [
    Column("username", types.Unicode(), nullable=False),
    Column("nickname", types.Unicode(), nullable=True),
]


@audit(context_columns=context_columns)
class Foo(Base):
    __tablename__ = "foo"

    id = Column(types.Integer(), primary_key=True)
    name = Column(types.Unicode())
    json = Column(JSONB())


register_sqlalchemy_events(Base.metadata, functions=True, triggers=True)

pg = create_postgres_fixture(engine_kwargs={"echo": True}, session=True)


def test_sets_session_values(pg):
    Base.metadata.create_all(bind=pg.connection())
    pg.commit()

    set_context_values(pg, username="foo@foo.com")
    pg.add(Foo(id=1, name=None, json=None))
    pg.commit()

    audit_row = pg.execute(Foo.__audit_table__.select()).fetchone()
    assert audit_row.audit_username == "foo@foo.com"


def test_sets_session_value_to_none(pg):
    Base.metadata.create_all(bind=pg.connection())
    pg.commit()

    set_context_values(pg, username="foo@foo.com", nickname=None)
    pg.add(Foo(id=1, name=None, json=None))
    pg.commit()

    audit_row = pg.execute(Foo.__audit_table__.select()).fetchone()
    assert audit_row.audit_username == "foo@foo.com"
    assert audit_row.audit_nickname is None


def test_fails_to_set_session_values(pg):
    Base.metadata.create_all(bind=pg.connection())
    pg.commit()

    pg.add(Foo(id=1, name=None, json=None))

    with pytest.raises(sqlalchemy.exc.ProgrammingError):
        pg.commit()
    pg.rollback()

    rows = pg.query(Foo).all()
    assert rows == []

    audit_rows = pg.execute(Foo.__audit_table__.select()).fetchall()
    assert audit_rows == []
