from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, text, types

from sqlalchemy_declarative_extensions import (
    declarative_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.dialects.postgresql import Procedure
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    procedures = [Procedure("gimme", "INSERT INTO foo VALUES (3);")]


class Foo(Base):
    __tablename__ = "foo"

    id = Column(types.Integer(), primary_key=True)


register_sqlalchemy_events(Base.metadata, procedures=True)

pg = create_postgres_fixture(engine_kwargs={"echo": True}, session=True)


def test_update(pg):
    pg.execute(text("CREATE TABLE foo (id INTEGER PRIMARY KEY)"))
    pg.execute(
        text(
            "CREATE procedure gimme() language sql as $$ INSERT INTO foo VALUES (1) $$;"
        )
    )
    pg.commit()

    Base.metadata.create_all(bind=pg.connection())
    pg.commit()

    pg.execute(text("CALL gimme()"))
    result = pg.execute(text("SELECT * FROM foo")).scalar()
    assert result == 3
