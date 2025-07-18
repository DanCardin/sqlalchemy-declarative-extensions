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

    schemas = ["table"]
    functions = Functions().are(
        Function(
            "gimme",
            """
            BEGIN
            INSERT INTO "table"."select" (id) select NEW.id + 1;
            RETURN NULL;
            END
            """,
            language="plpgsql",
            returns="trigger",
        )
    )
    triggers = Triggers().are(
        Trigger.after("insert", on="table.select", execute="gimme")
        .named("on_insert_foo")
        .when("pg_trigger_depth() < 1")
        .for_each_row(),
    )


class Foo(Base):
    __tablename__ = "select"
    __table_args__ = {"schema": "table"}

    id = Column(types.Integer(), primary_key=True)


register_sqlalchemy_events(Base.metadata, functions=True, triggers=True, schemas=True)

pg = create_postgres_fixture(engine_kwargs={"echo": True}, session=True)


def test_quotes_target_components(pg):
    Base.metadata.create_all(bind=pg.connection())
    pg.commit()

    pg.add(Foo(id=5))
    pg.commit()

    result = [r.id for r in pg.query(Foo).all()]
    assert result == [5, 6]

    connection = pg.connection()
    diff = compare_triggers(connection, Base.metadata.info["triggers"])
    assert diff == []
