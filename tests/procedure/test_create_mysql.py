from pytest_mock_resources import create_mysql_fixture
from sqlalchemy import Column, Integer, text

from sqlalchemy_declarative_extensions import (
    Procedure,
    Procedures,
    declarative_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.procedure.compare import compare_procedures
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    procedures = Procedures().are(
        Procedure(
            "gimme",
            "INSERT INTO foo (id) VALUES (DEFAULT);",
        ),
        # Ensure multiple statements arent normalized into different format
        Procedure(
            "gimme2",
            "BEGIN INSERT INTO foo (id) VALUES (DEFAULT); INSERT INTO foo (id) VALUES (DEFAULT); END",
        ),
        Procedure(
            "gimme3",
            """
            BEGIN
            INSERT INTO foo (id) VALUES (DEFAULT);
            INSERT INTO foo (id) VALUES (DEFAULT);
            END
            """,
        ),
    )


class Foo(Base):
    __tablename__ = "foo"

    id = Column(Integer, primary_key=True)


register_sqlalchemy_events(Base.metadata, procedures=True)

db = create_mysql_fixture(engine_kwargs={"echo": True}, session=True)


def test_create(db):
    Base.metadata.create_all(bind=db.connection())
    db.commit()

    db.execute(text("CALL gimme()"))
    db.execute(text("CALL gimme()"))

    result = db.execute(text("SELECT count(*) FROM foo")).scalar()
    assert result == 2

    db.execute(text("CALL gimme2()"))

    result = db.execute(text("SELECT count(*) FROM foo")).scalar()
    assert result == 4

    db.execute(text("CALL gimme3()"))
    result = db.execute(text("SELECT count(*) FROM foo")).scalar()
    assert result == 6

    connection = db.connection()
    diff = compare_procedures(connection, Base.metadata.info["procedures"])
    assert diff == []
