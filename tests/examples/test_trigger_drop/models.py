from sqlalchemy import Column, types

from sqlalchemy_declarative_extensions import Triggers, declarative_database
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    triggers = Triggers()


class Foo(Base):
    __tablename__ = "foo"

    id = Column(types.Integer(), primary_key=True)
