import pytest
import sqlalchemy.exc
from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import text

from sqlalchemy_declarative_extensions import (
    Procedures,
    declarative_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    procedures = Procedures()


register_sqlalchemy_events(Base.metadata, procedures=True)

pg = create_postgres_fixture(engine_kwargs={"echo": True}, session=True)


def test_delete(pg):
    pg.execute(text("CREATE procedure gimme() language sql as $$ select 1 $$;"))
    pg.commit()

    Base.metadata.create_all(bind=pg.connection())
    pg.commit()

    with pytest.raises(sqlalchemy.exc.ProgrammingError) as e:
        pg.execute(text("CALL gimme()")).scalar()
    assert "procedure gimme() does not exist" in str(e.value)
