from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, text, types

from sqlalchemy_declarative_extensions import (
    Triggers,
    declarative_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base
from sqlalchemy_declarative_extensions.trigger.compare import compare_triggers

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    triggers = Triggers(ignore_unspecified=True)


class Foo(Base):
    __tablename__ = "foo"

    id = Column(types.Integer(), primary_key=True)


register_sqlalchemy_events(Base.metadata, triggers=True)

pg = create_postgres_fixture(engine_kwargs={"echo": True}, session=True)


def test_drop(pg):
    pg.execute(text("CREATE TABLE foo (id integer primary key);"))
    pg.execute(
        text(
            """
            CREATE FUNCTION gimme() RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN
            INSERT INTO foo (id) select NEW.id + 1;
            RETURN NULL;
            END
            $$;
            """
        )
    )
    pg.execute(
        text(
            "CREATE TRIGGER on_insert_foo AFTER INSERT ON foo FOR EACH ROW "
            "WHEN (pg_trigger_depth() < 1) EXECUTE PROCEDURE gimme();"
        )
    )
    pg.commit()

    Base.metadata.create_all(bind=pg.connection())
    pg.commit()

    pg.add(Foo(id=5))
    pg.commit()

    result = [r.id for r in pg.query(Foo).all()]
    assert result == [5, 6]

    connection = pg.connection()
    diff = compare_triggers(connection, Base.metadata.info["triggers"])
    assert diff == []
