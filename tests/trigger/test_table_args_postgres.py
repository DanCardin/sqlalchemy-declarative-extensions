from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, types

from sqlalchemy_declarative_extensions import (
    Function,
    Functions,
    declarative_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.dialects.postgresql import Trigger
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base
from sqlalchemy_declarative_extensions.trigger.compare import compare_triggers

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    schemas = ["fancy"]
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
        ),
        Function(
            "noop",
            """
            BEGIN
            RETURN NULL;
            END
            """,
            language="plpgsql",
            returns="trigger",
        ),
    )


class Foo(Base):
    __tablename__ = "foo"
    __table_args__ = (
        Trigger.after("insert", execute="gimme")
        .named("on_insert_foo")
        .when("pg_trigger_depth() < 1")
        .for_each_row(),
    )

    id = Column(types.Integer(), primary_key=True)


class Bar(Base):
    __tablename__ = "bar"
    __table_args__ = (
        Trigger.after("insert", execute="noop").named("on_insert_bar").for_each_row(),
        {"schema": "fancy"},
    )

    id = Column(types.Integer(), primary_key=True)


register_sqlalchemy_events(Base.metadata, schemas=True, functions=True, triggers=True)

pg = create_postgres_fixture(engine_kwargs={"echo": True}, session=True)


def test_create(pg):
    Base.metadata.create_all(bind=pg.connection())
    pg.commit()

    pg.add(Foo(id=5))
    pg.add(Bar(id=1))
    pg.commit()

    assert [r.id for r in pg.query(Foo).all()] == [5, 6]
    assert [r.id for r in pg.query(Bar).all()] == [1]

    connection = pg.connection()
    diff = compare_triggers(connection, Base.metadata.info["triggers"])
    assert diff == []
