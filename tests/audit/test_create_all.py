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


@audit()
class Foo(Base):
    __tablename__ = "foo"

    id = Column(types.Integer(), primary_key=True)
    name = Column(types.Unicode())
    json = Column(JSONB())


register_sqlalchemy_events(Base.metadata, functions=True, triggers=True)

pg = create_postgres_fixture(engine_kwargs={"echo": True}, session=True)


def test_audit_table(pg):
    Base.metadata.create_all(bind=pg.connection())
    pg.commit()

    foo1 = Foo(id=1, name=None, json=None)
    foo2 = Foo(id=2, name=None, json={})
    pg.add(foo1)
    pg.add(foo2)
    pg.add(Foo(id=3, name="asdf", json=None))
    pg.add(Foo(id=4, name="qwer", json={"a": "a"}))
    pg.commit()

    foo1.name = "wow!"
    pg.delete(foo2)
    pg.commit()

    result = [f.id for f in pg.query(Foo).order_by(Foo.id.asc()).all()]
    assert result == [1, 3, 4]

    audit_rows = pg.execute(Foo.__audit_table__.select()).fetchall()
    audit_rows = [(a, b, *c) for a, b, _, *c in audit_rows]
    assert audit_rows == [
        (1, "I", "user", 1, None, None),
        (2, "I", "user", 2, None, {}),
        (3, "I", "user", 3, "asdf", None),
        (4, "I", "user", 4, "qwer", {"a": "a"}),
        (5, "U", "user", 1, "wow!", None),
        (6, "D", "user", 2, None, {}),
    ]
