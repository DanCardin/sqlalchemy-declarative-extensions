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
from sqlalchemy_declarative_extensions.trigger.compare import compare_triggers

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    functions = Functions().are(
        Function(
            "count_arguments",
            """
            DECLARE
                arg_name TEXT;
            BEGIN
                FOREACH arg_name in ARRAY TG_ARGV LOOP
                    RAISE NOTICE 'Processing %', arg_name;
                    UPDATE foo SET arg_count = arg_count + 1 WHERE id = NEW.id;
                END LOOP;
            RETURN NEW;
            END
            """,
            language="plpgsql",
            returns="trigger",
        )
    )
    triggers = Triggers().are(
        Trigger.after("insert", on="foo", execute="count_arguments")
        .named("on_insert_foo_single")
        .for_each_row()
        .with_arguments("single"),
        Trigger.after("insert", on="foo", execute="count_arguments")
        .named("on_insert_foo_multi")
        .for_each_row()
        .with_arguments("multi1", "multi2"),
    )


class Foo(Base):
    __tablename__ = "foo"

    id = Column(types.Integer(), primary_key=True)
    arg_count = Column(types.Integer(), default=0)


register_sqlalchemy_events(Base.metadata, functions=True, triggers=True)

pg = create_postgres_fixture(engine_kwargs={"echo": True}, session=True)


def test_create(pg):
    Base.metadata.create_all(bind=pg.connection())
    pg.commit()

    pg.add(Foo(id=5))
    pg.add(Foo(id=7))
    pg.commit()

    result = [(r.id, r.arg_count) for r in pg.query(Foo).all()]
    assert result == [(5, 3), (7, 3)]

    connection = pg.connection()
    diff = compare_triggers(connection, Base.metadata.info["triggers"])
    assert diff == []
