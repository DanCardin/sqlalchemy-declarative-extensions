from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, types
from sqlalchemy.dialects.postgresql import JSONB

from sqlalchemy_declarative_extensions import (
    declarative_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.audit import audit
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True


@audit(insert=False)
@declarative_database
class Foo(Base):
    __tablename__ = "foo"

    id = Column(types.Integer(), primary_key=True)
    name = Column(types.Unicode())
    json = Column(JSONB())


register_sqlalchemy_events(Base.metadata, functions=True, triggers=True)

pg = create_postgres_fixture(engine_kwargs={"echo": True}, session=True)


def test_disabled_insert_events(pg):
    Base.metadata.create_all(bind=pg.connection())
    pg.commit()

    foo = Foo(id=1, name=None, json=None)
    pg.add(foo)
    pg.commit()

    foo.name = "asdf"
    pg.commit()

    audit_row = pg.execute(Foo.__audit_table__.select()).fetchone()
    assert audit_row.audit_operation == "U"
    assert audit_row.name == "asdf"
