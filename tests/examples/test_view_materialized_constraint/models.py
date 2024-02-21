import sqlalchemy
from sqlalchemy import Column, Index, UniqueConstraint, types

from sqlalchemy_declarative_extensions import ViewIndex, declarative_database, view
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base, select

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True


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
    __table_args__ = (UniqueConstraint("num", "num2"),)

    num = Column(types.Integer(), nullable=False)
    num2 = Column(types.Integer(), nullable=False)


@view(Base, materialized=True)
class Bax:
    __tablename__ = "bax"
    __view__ = select(foo_table.c.num, foo_table.c.num2).where(foo_table.c.id <= 10)
    __table_args__ = (
        ViewIndex(
            ["num", "num2"],
            name="uq_bax",
        ),
    )

    num = Column(types.Integer(), nullable=False)
    num2 = Column(types.Integer(), nullable=False)
