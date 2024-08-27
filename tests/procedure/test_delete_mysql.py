import pytest
import sqlalchemy.exc
from pytest_mock_resources import create_mysql_fixture
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

db = create_mysql_fixture(engine_kwargs={"echo": True}, session=True)


def test_delete(db):
    db.execute(text("CREATE PROCEDURE gimme() SELECT 1"))
    db.commit()

    Base.metadata.create_all(bind=db.connection())
    db.commit()

    with pytest.raises(sqlalchemy.exc.OperationalError) as e:
        db.execute(text("CALL gimme()")).scalar()
    assert "gimme does not exist" in str(e.value)
