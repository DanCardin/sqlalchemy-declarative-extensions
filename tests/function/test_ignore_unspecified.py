from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import text

from sqlalchemy_declarative_extensions import (
    Functions,
    declarative_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    functions = Functions(ignore_unspecified=True)


register_sqlalchemy_events(Base.metadata, functions=True)

pg = create_postgres_fixture(engine_kwargs={"echo": True}, session=True)


def test_delete(pg):
    pg.execute(
        text("CREATE FUNCTION gimme() RETURNS INTEGER language sql as $$ select 1 $$;")
    )
    pg.commit()

    Base.metadata.create_all(bind=pg.connection())
    pg.commit()

    result = pg.execute(text("SELECT gimme()")).scalar()
    assert result == 1
