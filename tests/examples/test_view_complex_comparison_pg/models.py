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
class Base(_Base):
    __abstract__ = True

    schemas = Schemas().are("namespace")
    rows = [Row("namespace.foo", id=3)]
    views = Views().are(
        View(
            "baz",
            "select id, foo_id from namespace.foo join namespace.bar on namespace.foo.id = namespace.bar.foo_id",
            schema="namespace",
        )
    )


class Foo(Base):
    __tablename__ = "foo"
    __table_args__ = {"schema": "namespace"}

    id = Column(types.Integer(), autoincrement=True, primary_key=True)


class Bar(Base):
    __tablename__ = "bar"
    __table_args__ = {"schema": "namespace"}

    foo_id = Column(types.Integer(), ForeignKey("namespace.foo.id"), primary_key=True)
