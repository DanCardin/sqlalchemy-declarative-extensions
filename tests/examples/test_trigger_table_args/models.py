from sqlalchemy import Column, types

from sqlalchemy_declarative_extensions import declarative_database
from sqlalchemy_declarative_extensions.dialects.postgresql import Trigger
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True


class Foo(Base):
    __tablename__ = "foo"
    __table_args__ = (
        Trigger.after("insert", execute="gimme")
        .named("on_insert_foo")
        .when("pg_trigger_depth() < 1")
        .for_each_row(),
    )

    id = Column(types.Integer(), primary_key=True)
