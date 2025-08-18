from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, text, types

from sqlalchemy_declarative_extensions import (
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

    triggers = Triggers().are(
        Trigger.after("update", on="foo", execute="gimme")
        .named("on_insert_foo")
        .when("pg_trigger_depth() < 1")
        .for_each_statement()
        .referencing_old_table_as("old_foo")
        .referencing_new_table_as("new_foo")
        .with_arguments("declarative!"),
    )


class Foo(Base):
    __tablename__ = "foo"

    id = Column(types.Integer(), primary_key=True)
    extra = Column(types.String(), nullable=True)


register_sqlalchemy_events(Base.metadata, triggers=True)

pg = create_postgres_fixture(engine_kwargs={"echo": True}, session=True)


def test_update(pg):
    pg.execute(text("CREATE TABLE foo (id integer primary key, extra text);"))
    pg.execute(
        text(
            """
            CREATE FUNCTION gimme() RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN
            -- Read the extra from TG_ARGV
            INSERT INTO foo (id, extra) SELECT new_foo.id + 1, TG_ARGV[0] FROM new_foo;
            RETURN NULL;
            END
            $$;
            """
        )
    )
    pg.execute(
        text(
            "CREATE TRIGGER on_insert_foo AFTER INSERT ON foo REFERENCING NEW TABLE AS new_foo FOR EACH STATEMENT "
            "WHEN (pg_trigger_depth() < 1) EXECUTE PROCEDURE gimme();"
        )
    )
    pg.commit()

    pg.add(Foo(id=5))
    pg.commit()

    result = [(r.id, r.extra) for r in pg.query(Foo).all()]
    assert result == [(5, None), (6, None)]

    Base.metadata.create_all(bind=pg.connection())
    pg.commit()

    foo = Foo(id=9)
    pg.add(foo)
    pg.commit()

    result = [(r.id, r.extra) for r in pg.query(Foo).all()]
    assert result == [(5, None), (6, None), (9, None)]

    foo.id = 10
    pg.commit()
    result = [(r.id, r.extra) for r in pg.query(Foo).all()]
    assert result == [(5, None), (6, None), (10, None), (11, "declarative!")]

    connection = pg.connection()
    diff = compare_triggers(connection, Base.metadata.info["triggers"])
    assert diff == []
