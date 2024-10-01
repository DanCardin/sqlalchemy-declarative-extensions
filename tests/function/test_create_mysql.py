from pytest_mock_resources import create_mysql_fixture
from sqlalchemy import Column, Integer, text

from sqlalchemy_declarative_extensions import (
    Functions,
    declarative_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.dialects.mysql import Function
from sqlalchemy_declarative_extensions.function.compare import compare_functions
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    functions = Functions().are(
        Function(
            "gimme",
            """
            BEGIN
            INSERT INTO foo (id) VALUES (DEFAULT);
            RETURN (SELECT count(*) FROM foo);
            END
            """,
            returns="INTEGER",
        ).modifies_sql()
    )


class Foo(Base):
    __tablename__ = "foo"

    id = Column(Integer, primary_key=True)


register_sqlalchemy_events(Base.metadata, functions=True)

db = create_mysql_fixture(engine_kwargs={"echo": True}, session=True)


def test_create(db):
    db.execute(text("SET GLOBAL log_bin_trust_function_creators = ON;"))

    Base.metadata.create_all(bind=db.connection())
    db.commit()

    result = db.execute(text("SELECT gimme()")).scalar()
    assert result == 1

    result = db.execute(text("SELECT gimme()")).scalar()
    assert result == 2

    connection = db.connection()
    diff = compare_functions(connection, Base.metadata.info["functions"])
    assert diff == []
