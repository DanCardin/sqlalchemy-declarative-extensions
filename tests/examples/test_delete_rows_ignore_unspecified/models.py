from sqlalchemy import Column, types
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_declarative_extensions import Row, Rows, declarative_database

_Base = declarative_base()


@declarative_database
class Base(_Base):
    __abstract__ = True

    rows = Rows(ignore_unspecified=True).are(
        Row("foo", id=2, name="asdf"),
        Row("foo", id=3, name="qwer", active=False),
    )


class Foo(Base):
    __tablename__ = "foo"

    id = Column(types.Integer(), primary_key=True)
    name = Column(types.Unicode(), nullable=False)
    active = Column(types.Boolean())
