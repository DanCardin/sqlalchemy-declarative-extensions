from pytest_mock_resources import create_mysql_fixture
from sqlalchemy import Column, text, types

from sqlalchemy_declarative_extensions import (
    Triggers,
    declarative_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.dialects.mysql import Trigger
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base
from sqlalchemy_declarative_extensions.trigger.compare import compare_triggers

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    triggers = Triggers().are(
        Trigger.before("INSERT", on="foo", execute="SET NEW.id = NEW.id + 10").named(
            "on_insert_foo"
        )
    )


class Foo(Base):
    __tablename__ = "foo"

    id = Column(types.Integer(), primary_key=True)


register_sqlalchemy_events(Base.metadata, triggers=True)

pg = create_mysql_fixture(engine_kwargs={"echo": True}, session=True)


def test_update(pg):
    pg.execute(text("CREATE TABLE foo (id integer primary key);"))
    pg.execute(
        text(
            "CREATE TRIGGER gimme BEFORE INSERT ON foo FOR EACH ROW SET NEW.id = NEW.id + 1;"
        )
    )
    pg.commit()

    # Prove the trigger exists with old value
    pg.add(Foo(id=5))
    pg.commit()
    result = [r.id for r in pg.query(Foo).all()]
    assert result == [6]

    # Update it
    Base.metadata.create_all(bind=pg.connection())
    pg.commit()

    # Prove the trigger exists with new value
    foo = Foo(id=5)
    pg.add(foo)
    pg.commit()
    result = [r.id for r in pg.query(Foo).all()]
    assert result == [6, 15]

    connection = pg.connection()
    diff = compare_triggers(connection, Base.metadata.info["triggers"])
    assert diff == []
