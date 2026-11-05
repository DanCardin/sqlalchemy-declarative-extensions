from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, text, types

from sqlalchemy_declarative_extensions import (
    Functions,
    declarative_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.dialects.postgresql import (
    Trigger,
    trigger_function,
)
from sqlalchemy_declarative_extensions.function.compare import (
    DropFunctionOp,
    compare_functions,
)
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base
from sqlalchemy_declarative_extensions.trigger.compare import compare_triggers

_Base = declarative_base()

audit = trigger_function(
    "audit",
    """
    BEGIN
    INSERT INTO log (message) VALUES (TG_TABLE_NAME);
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
    message = Column(types.String())


class Foo(Base):
    __tablename__ = "foo"
    __table_args__ = (
        Trigger.after("insert", execute=audit).named("on_insert_foo").for_each_row(),
    )

    id = Column(types.Integer(), primary_key=True)


class Bar(Base):
    __tablename__ = "bar"
    __table_args__ = (
        Trigger.after("insert", execute=audit).named("on_insert_bar").for_each_row(),
    )

    id = Column(types.Integer(), primary_key=True)


register_sqlalchemy_events(Base.metadata, functions=True, triggers=True)

pg = create_postgres_fixture(engine_kwargs={"echo": True}, session=True)


def _audit_count(connection):
    return connection.execute(
        text("SELECT count(*) FROM pg_proc WHERE proname = 'audit'")
    ).scalar()


def test_shared_function_is_created_once_and_fires(pg):
    Base.metadata.create_all(bind=pg.connection())
    pg.commit()

    pg.add(Foo(id=1))
    pg.add(Bar(id=1))
    pg.commit()

    assert sorted(r.message for r in pg.query(Log).all()) == ["bar", "foo"]

    connection = pg.connection()
    assert compare_functions(connection, Functions.extract(Base.metadata)) == []
    assert compare_triggers(connection, Base.metadata.info["triggers"]) == []


def test_drop_all_drops_the_function(pg):
    connection = pg.connection()
    Base.metadata.create_all(bind=connection)
    assert _audit_count(connection) == 1

    Base.metadata.drop_all(bind=connection)
    assert _audit_count(connection) == 0


def test_unrelated_functions_are_left_alone(pg):
    pg.execute(text("CREATE FUNCTION other() RETURNS int LANGUAGE sql AS 'SELECT 1';"))
    pg.commit()

    ops = compare_functions(pg.connection(), Functions.extract(Base.metadata))
    assert not [op for op in ops if isinstance(op, DropFunctionOp)]
