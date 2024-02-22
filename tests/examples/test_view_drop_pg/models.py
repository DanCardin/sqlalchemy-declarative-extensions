import sqlalchemy
from sqlalchemy import Column, types

from sqlalchemy_declarative_extensions import Row, declarative_database
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    rows = [
        Row("foo", id=3),
        Row("foo", id=10),
        Row("foo", id=11),
        Row("foo", id=12),
    ]
    views = []


class Foo(Base):
    __tablename__ = "foo"

    id = Column(types.Integer(), autoincrement=True, primary_key=True)

    created_at = sqlalchemy.Column(
        sqlalchemy.types.DateTime(timezone=True),
        server_default=sqlalchemy.text("CURRENT_TIMESTAMP"),
        nullable=False,
    )


foo_table = Foo.__table__
