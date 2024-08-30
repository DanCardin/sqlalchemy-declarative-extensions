from pytest_mock_resources import create_mysql_fixture
from sqlalchemy import text

from sqlalchemy_declarative_extensions import (
    declarative_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.dialects.mysql import Function
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    functions = [
        Function("gimme", "RETURN true", returns="boolean", deterministic=True)
    ]


register_sqlalchemy_events(Base.metadata, functions=True)

pg = create_mysql_fixture(engine_kwargs={"echo": True}, session=True)


def test_update(pg):
    pg.execute(text("CREATE FUNCTION gimme() RETURNS bool DETERMINISTIC RETURN FALSE;"))
    pg.commit()

    result = pg.execute(text("SELECT gimme()")).scalar()
    assert result == 0

    Base.metadata.create_all(bind=pg.connection())
    pg.commit()

    result = pg.execute(text("SELECT gimme()")).scalar()
    assert result == 1
