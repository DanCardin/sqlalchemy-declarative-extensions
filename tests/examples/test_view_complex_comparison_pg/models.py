from sqlalchemy import Column, ForeignKey, types

from sqlalchemy_declarative_extensions import (
    Row,
    Schemas,
    View,
    Views,
    declarative_database,
)
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    schemas = Schemas().are("wat")
    rows = [Row("wat.foo", id=3)]
    views = Views().are(
        View(
            "baz",
            "select id, foo_id from wat.foo join wat.bar on wat.foo.id = wat.bar.foo_id",
            schema="wat",
        )
    )


class Foo(Base):
    __tablename__ = "foo"
    __table_args__ = {"schema": "wat"}

    id = Column(types.Integer(), autoincrement=True, primary_key=True)


class Bar(Base):
    __tablename__ = "bar"
    __table_args__ = {"schema": "wat"}

    foo_id = Column(types.Integer(), ForeignKey("wat.foo.id"), primary_key=True)
