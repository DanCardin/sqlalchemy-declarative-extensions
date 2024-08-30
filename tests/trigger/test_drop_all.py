from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, types

from sqlalchemy_declarative_extensions import (
    Function,
    Functions,
    Triggers,
    declarative_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.dialects.postgresql import Trigger
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    functions = Functions().are(
        Function(
            "gimme",
            """
            BEGIN
            INSERT INTO foo (id) select NEW.id + 1;
            RETURN NULL;
            END
            """,
            language="plpgsql",
            returns="trigger",
        )
    )
    triggers = Triggers().are(
        Trigger.after("insert", on="foo", execute="gimme")
        .named("on_insert_foo")
        .when("pg_trigger_depth() < 1")
        .for_each_row(),
    )


class Foo(Base):
    __tablename__ = "foo"

    id = Column(types.Integer(), primary_key=True)


register_sqlalchemy_events(Base.metadata, functions=True, triggers=True)

pg = create_postgres_fixture(engine_kwargs={"echo": True}, session=True)


def test_create(pg):
    Base.metadata.create_all(bind=pg.connection())
    Base.metadata.drop_all(bind=pg.connection())
