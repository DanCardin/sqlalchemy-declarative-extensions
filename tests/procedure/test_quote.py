from pytest_mock_resources import create_postgres_fixture
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
            "table",
            "INSERT INTO foo (id) VALUES (DEFAULT);",
        )
    )


class Foo(Base):
    __tablename__ = "foo"

    id = Column(Integer, primary_key=True)


register_sqlalchemy_events(Base.metadata, procedures=True)

pg = create_postgres_fixture(engine_kwargs={"echo": True}, session=True)


def test_create(pg):
    Base.metadata.create_all(bind=pg.connection())
    pg.commit()

    pg.execute(text('CALL "table"()'))
    pg.execute(text('CALL "table"()'))

    result = pg.execute(text("SELECT count(*) FROM foo")).scalar()
    assert result == 2

    connection = pg.connection()
    diff = compare_procedures(connection, Base.metadata.info["procedures"])
    assert diff == []
