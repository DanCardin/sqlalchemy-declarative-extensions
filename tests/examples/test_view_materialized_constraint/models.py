import sqlalchemy
from sqlalchemy import Column, Index, select, types
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_declarative_extensions import Row, declarative_database, view

_Base = declarative_base()


@declarative_database()
class Base(_Base):
    __abstract__ = True

    rows = [
        Row("foo", num=1, num2=1, id=3),
        Row("foo", num=2, num2=1, id=10),
        Row("foo", num=3, num2=1, id=11),
        Row("foo", num=3, num2=1, id=12),
    ]


class Foo(Base):
    __tablename__ = "foo"

    id = Column(types.Integer(), autoincrement=True, primary_key=True)
    num = Column(types.Integer(), nullable=False)
    num2 = Column(types.Integer(), nullable=False)

    created_at = sqlalchemy.Column(
        sqlalchemy.types.DateTime(timezone=True),
        server_default=sqlalchemy.text("CURRENT_TIMESTAMP"),
        nullable=False,
    )


foo_table = Foo.__table__


@view(Base, materialized=True)
class Bar:
    __tablename__ = "bar"
    __view__ = select(foo_table.c.num, foo_table.c.num2).where(foo_table.c.id > 10)
    __table_args__ = (Index("uq_bar", "num", "num2", unique=True),)

    num = Column(types.Integer(), nullable=False)
    num2 = Column(types.Integer(), nullable=False)


@view(Base, materialized=True)
class Baz:
    __tablename__ = "baz"
    __view__ = select(foo_table.c.num, foo_table.c.num2).where(foo_table.c.id <= 10)
    __table_args__ = (Index("uq_baz", "num", "num2", unique=True),)

    num = Column(types.Integer(), nullable=False)
    num2 = Column(types.Integer(), nullable=False)
