import pytest
from sqlalchemy import Column, types

from sqlalchemy_declarative_extensions import (
    Triggers,
    declare_database,
)
from sqlalchemy_declarative_extensions.dialects.postgresql import Trigger
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base


def create_base(triggers=None):
    declarative = declarative_base()

    class Base(declarative):  # type: ignore
        __abstract__ = True

    declare_database(Base.metadata, triggers=triggers)
    return Base


def test_on_inferred_from_table():
    base = create_base()

    class Foo(base):
        __tablename__ = "foo"
        __table_args__ = (
            Trigger.after("insert", execute="gimme")
            .named("on_insert_foo")
            .for_each_row(),
        )

        id = Column(types.Integer(), primary_key=True)

    triggers = Triggers.extract(base.metadata)

    expected_triggers = Triggers().are(
        Trigger.after("insert", on="foo", execute="gimme")
        .named("on_insert_foo")
        .for_each_row()
    )
    assert triggers == expected_triggers


def test_on_inferred_from_schema_qualified_table():
    base = create_base()

    class Foo(base):
        __tablename__ = "select"
        __table_args__ = (
            Trigger.after("insert", execute="gimme").named("on_insert_foo"),
            {"schema": "table"},
        )

        id = Column(types.Integer(), primary_key=True)

    (trigger,) = Triggers.extract(base.metadata)
    assert trigger.on == "table.select"
    assert trigger.identity == ("table.select", "on_insert_foo")


def test_combines_with_metadata_triggers():
    base = create_base(
        triggers=Triggers(ignore_unspecified=True, ignore=["ignored"]).are(
            Trigger.after("insert", on="bar", execute="gimme").named("on_insert_bar")
        )
    )

    class Foo(base):
        __tablename__ = "foo"
        __table_args__ = (
            Trigger.after("insert", execute="gimme").named("on_insert_foo"),
        )

        id = Column(types.Integer(), primary_key=True)

    triggers = Triggers.extract(base.metadata)
    assert triggers.ignore_unspecified is True
    assert triggers.ignore == ["ignored"]

    trigger_ids = [t.identity for t in triggers]
    assert trigger_ids == [("bar", "on_insert_bar"), ("foo", "on_insert_foo")]


def test_shared_trigger_is_not_mutated():
    base = create_base()

    trigger = Trigger.after("insert", execute="gimme").named("on_insert")

    class Foo(base):
        __tablename__ = "foo"
        __table_args__ = (trigger,)

        id = Column(types.Integer(), primary_key=True)

    class Bar(base):
        __tablename__ = "bar"
        __table_args__ = (trigger,)

        id = Column(types.Integer(), primary_key=True)

    assert trigger.on == ""

    trigger_ids = [t.identity for t in Triggers.extract(base.metadata)]
    assert trigger_ids == [("foo", "on_insert"), ("bar", "on_insert")]


def test_requires_a_name():
    base = create_base()

    with pytest.raises(ValueError, match="must have a name"):

        class Foo(base):
            __tablename__ = "foo"
            __table_args__ = (Trigger.after("insert", execute="gimme"),)

            id = Column(types.Integer(), primary_key=True)


def test_conflicting_on():
    base = create_base()

    with pytest.raises(ValueError, match="conflicts with the table"):

        class Foo(base):
            __tablename__ = "foo"
            __table_args__ = (
                Trigger.after("insert", on="bar", execute="gimme").named("on_insert"),
            )

            id = Column(types.Integer(), primary_key=True)
