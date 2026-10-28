from collections import namedtuple

import pytest
from sqlalchemy import Column, text, types
from sqlalchemy.engine import Engine

from sqlalchemy_declarative_extensions import (
    declarative_database,
    register_sqlalchemy_events,
    view,
)
from sqlalchemy_declarative_extensions.dialects.snowflake.query import (
    get_views_snowflake,
)
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    schemas = ["foo"]


@view(Base, register_as_model=True)
class Bar:
    __tablename__ = "bar"
    __table_args__ = {"schema": "foo"}
    __view__ = (
        "select table_catalog, table_schema, table_name from information_schema.views"
    )

    id = Column(types.Integer(), primary_key=True)


register_sqlalchemy_events(Base.metadata, schemas=True, views=True)


def test_create_view_snowflake(snowflake: Engine):
    Base.metadata.create_all(bind=snowflake)

    with snowflake.connect() as conn:
        result = conn.execute(text("select * from foo.bar")).all()
    assert result == [("TEST", "FOO", "BAR")]


def test_update_view_snowflake(snowflake: Engine):
    with snowflake.connect() as conn:
        conn.execute(text("CREATE SCHEMA foo"))
        conn.execute(
            text(
                "CREATE VIEW foo.bar AS SELECT table_schema FROM information_schema.views"
            )
        )

    with snowflake.connect() as conn:
        result = conn.execute(text("select * from foo.bar")).all()
    assert result == [("FOO",)]

    Base.metadata.create_all(bind=snowflake)

    with snowflake.connect() as conn:
        result = conn.execute(text("select * from foo.bar")).all()
    assert result == [("TEST", "FOO", "BAR")]


Row = namedtuple("Row", ["schema", "name", "definition"])


class StubConnection:
    def __init__(self, rows):
        self.rows = rows

    def execute(self, *args, **kwargs):
        rows = self.rows

        class Result:
            def fetchall(self):
                return rows

        return Result()


def test_get_views_warns_and_skips_views_without_visible_definition():
    connection = StubConnection(
        [
            Row("FOO", "hidden", None),
            Row("FOO", "visible", "CREATE VIEW foo.visible AS select 1"),
        ]
    )

    with pytest.warns(UserWarning, match="Skipping view 'FOO.hidden'"):
        views = get_views_snowflake(connection)  # type: ignore

    assert [(v.schema, v.name) for v in views] == [("FOO", "visible")]


def test_get_views_does_not_inspect_ignored_views():
    connection = StubConnection(
        [
            # Neither would be valid to introspect, but they're ignored (case insensitively).
            Row("FOO", "hidden", None),
            Row("OTHER", "weird", "CREATE SECURE VIEW other.weird AS select 1"),
            Row("FOO", "visible", "CREATE VIEW foo.visible AS select 1"),
        ]
    )

    views = get_views_snowflake(connection, ignore=["foo.hidden", "other.*"])  # type: ignore

    assert [(v.schema, v.name) for v in views] == [("FOO", "visible")]


def test_get_views_only_inspects_included_views():
    connection = StubConnection(
        [
            Row("OTHER", "hidden", None),
            Row("FOO", "visible", "CREATE VIEW foo.visible AS select 1"),
        ]
    )

    # No warning for the view which is not visible: it is outside of `include`.
    views = get_views_snowflake(connection, include=["foo.*"])  # type: ignore

    assert [(v.schema, v.name) for v in views] == [("FOO", "visible")]
