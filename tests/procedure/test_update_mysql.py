from pytest_mock_resources import create_mysql_fixture
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

db = create_mysql_fixture(engine_kwargs={"echo": True}, session=True)


def test_update(db):
    db.execute(text("CREATE TABLE foo (id INTEGER PRIMARY KEY)"))
    db.execute(text("CREATE procedure gimme() INSERT INTO foo VALUES (1);"))
    db.commit()

    Base.metadata.create_all(bind=db.connection())
    db.commit()

    db.execute(text("CALL gimme()"))
    result = db.execute(text("SELECT * FROM foo")).scalar()
    assert result == 3
