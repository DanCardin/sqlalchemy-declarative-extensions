from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, text, types

from sqlalchemy_declarative_extensions import (
    declarative_database,
    register_sqlalchemy_events,
    view,
)
from sqlalchemy_declarative_extensions.alembic.view import UpdateViewOp
from sqlalchemy_declarative_extensions.dialects import postgresql
from sqlalchemy_declarative_extensions.dialects.postgresql import View
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base
from sqlalchemy_declarative_extensions.view.compare import compare_views

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True


class Foo(Base):
    __tablename__ = "foo"

    id = Column(types.String(), primary_key=True)


@view(Base)
class Bar:
    __tablename__ = "bar"
    __view__ = r"SELECT id::text FROM foo WHERE id like '\:foo %s %(id)s'"


register_sqlalchemy_events(Base.metadata, views=True)

pg = create_postgres_fixture(
    scope="function", engine_kwargs={"echo": True}, session=True
)


def test_escape_bindparam_postgres(pg):
    Base.metadata.create_all(bind=pg.connection())
    pg.commit()

    result = pg.execute(text("select * from bar")).fetchall()
    assert result == []

    # Make sure that bindparams escaping doesn't create unnecessary escapes
    # for the literal casts that appear after view definition round-tripping
    rendered = View("simple_select", "SELECT 'a' as col1").render_definition(pg.connection())
    assert "::" in rendered, "Literals in the view definition are expected to get explicit type casts"
    assert "\\:\\:" not in rendered, "Bind parameters escaping should leave type casts unescaped"
