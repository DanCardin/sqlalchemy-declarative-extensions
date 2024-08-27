import pytest
import sqlalchemy.exc
from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import text

from sqlalchemy_declarative_extensions import (
    Function,
    Functions,
    declarative_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    functions = Functions().are(
        Function(
            "gimme",
            "SELECT 1",
            returns="INTEGER",
        )
    )


register_sqlalchemy_events(Base.metadata, functions=True)

pg = create_postgres_fixture(engine_kwargs={"echo": True}, session=True)


def test_create(pg):
    Base.metadata.create_all(bind=pg.connection())

    result = pg.execute(text("SELECT gimme()")).scalar()
    assert result == 1

    Base.metadata.drop_all(bind=pg.connection())
    with pytest.raises(sqlalchemy.exc.ProgrammingError):
        pg.execute(text("SELECT gimme()")).scalar()
