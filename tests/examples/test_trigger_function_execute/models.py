from sqlalchemy import Column, types

from sqlalchemy_declarative_extensions import declarative_database
from sqlalchemy_declarative_extensions.dialects.postgresql import (
    Trigger,
    trigger_function,
)
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()

gimme = trigger_function(
    "gimme",
    """
    BEGIN
    INSERT INTO log (id) select NEW.id + 1;
    RETURN NULL;
    END
    """,
)


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True


class Log(Base):
    __tablename__ = "log"

    id = Column(types.Integer(), primary_key=True)


class Foo(Base):
    __tablename__ = "foo"
    __table_args__ = (
        Trigger.after("insert", execute=gimme).named("on_insert_foo").for_each_row(),
    )

    id = Column(types.Integer(), primary_key=True)


class Bar(Base):
    __tablename__ = "bar"
    __table_args__ = (
        Trigger.after("insert", execute=gimme).named("on_insert_bar").for_each_row(),
    )

    id = Column(types.Integer(), primary_key=True)
