import pytest
from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

from sqlalchemy_declarative_extensions import (
    Procedure,
    Procedures,
    declarative_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    procedures = Procedures().are(
        Procedure(
            "gimme",
            "SELECT 1;",
        )
    )


register_sqlalchemy_events(Base.metadata, procedures=True)

pg = create_postgres_fixture(engine_kwargs={"echo": True}, session=True)


def test_create(pg):
    Base.metadata.create_all(bind=pg.connection())

    pg.execute(text("CALL gimme()"))

    Base.metadata.drop_all(bind=pg.connection())

    with pytest.raises(ProgrammingError):
        pg.execute(text("CALL gimme()"))
