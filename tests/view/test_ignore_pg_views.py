from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import text

from sqlalchemy_declarative_extensions import (
    Views,
    declarative_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base
from tests import skip_sqlalchemy13

()


_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    views = Views()


register_sqlalchemy_events(Base.metadata, views=True)

pg = create_postgres_fixture(
    scope="function", engine_kwargs={"echo": True}, session=True
)


@skip_sqlalchemy13
def test_ignore_pg_views(pg):
    """Assert that we ignore built-in postgres views.

    By default there are none outside information_schema/pg_* schemas, however
    one can load plugins, such as pg_stat_statements, which should be ignored
    regardless.
    """
    pg.execute(text("CREATE VIEW pg_stat_statements AS (SELECT rolname from pg_roles)"))

    Base.metadata.create_all(bind=pg.connection())

    # I.e. assert we did not drop the view.
    pg.execute(text("SELECT * FROM pg_stat_statements")).all()
