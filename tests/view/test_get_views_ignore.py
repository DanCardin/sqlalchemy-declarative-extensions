from pytest_mock_resources import create_sqlite_fixture
from sqlalchemy import MetaData, text

from sqlalchemy_declarative_extensions.dialects.sqlite.query import get_views_sqlite
from sqlalchemy_declarative_extensions.sql import filter_ignored, is_ignored
from sqlalchemy_declarative_extensions.view.base import View, Views
from sqlalchemy_declarative_extensions.view.compare import (
    DropViewOp,
    UpdateViewOp,
    compare_views,
)

sqlite = create_sqlite_fixture()


def test_is_ignored_globs():
    assert is_ignored("foo.bar", ["foo.*"])
    assert is_ignored("foo.bar", ["nope", "*.bar"])
    assert not is_ignored("foo.bar", ["baz.*"])
    assert not is_ignored("foo.bar", [])


def test_is_ignored_case_sensitivity():
    assert not is_ignored("FOO.BAR", ["foo.*"])
    assert is_ignored("FOO.BAR", ["foo.*"], case_sensitive=False)


def test_filter_ignored_uses_qualified_names():
    views = [View("a", "select 1"), View("b", "select 1", schema="foo")]

    assert [v.qualified_name for v in filter_ignored(views, ["foo.*"])] == ["a"]
    assert filter_ignored(views, []) == views


def test_get_views_sqlite_ignores(sqlite):
    with sqlite.connect() as connection:
        connection.execute(text("create view keep as select 1 as x"))
        connection.execute(text("create view skip_me as select 1 as x"))

        assert {v.name for v in get_views_sqlite(connection)} == {"keep", "skip_me"}
        assert {v.name for v in get_views_sqlite(connection, ignore=["skip_*"])} == {
            "keep"
        }


def test_is_ignored_include():
    assert not is_ignored("foo.bar", [], include=["foo.*"])
    assert is_ignored("baz.bar", [], include=["foo.*"])
    assert is_ignored("foo.bar", [], include=[])

    # Unset include does not restrict anything. Ignore still applies on top of include.
    assert not is_ignored("baz.bar", [], include=None)
    assert is_ignored("foo.bar", ["*.bar"], include=["foo.*"])
    assert is_ignored("BAZ.BAR", [], include=["foo.*"], case_sensitive=False)
    assert not is_ignored("FOO.BAR", [], include=["foo.*"], case_sensitive=False)


def test_get_views_sqlite_includes(sqlite):
    with sqlite.connect() as connection:
        connection.execute(text("create view keep_a as select 1 as x"))
        connection.execute(text("create view other_b as select 1 as x"))

        assert {v.name for v in get_views_sqlite(connection, include=["keep_*"])} == {
            "keep_a"
        }


def test_compare_views_include_only_manages_matching_views(sqlite):
    with sqlite.connect() as connection:
        connection.execute(text("create view keep_old as select 1 as x"))
        connection.execute(text("create view other_view as select 1 as x"))

        ops = compare_views(connection, Views(include=["keep_*"]))
        assert [(type(op), op.view.name) for op in ops] == [(DropViewOp, "keep_old")]  # type: ignore

        assert compare_views(connection, Views()) != []
        assert compare_views(connection, Views(include=["keep_*"], ignore=["*"])) == []


def test_compare_views_include_still_compares_declared_views(sqlite):
    with sqlite.connect() as connection:
        connection.execute(text("create view other_view as select 1 as x"))

        # A declared view outside of `include` exists already, so it is found and compared
        # (sqlite stores the full `CREATE VIEW` text, hence the update), not created again.
        views = Views(include=["keep_*"]).are(View("other_view", "select 1 as x"))
        assert [type(op) for op in compare_views(connection, views)] == [UpdateViewOp]


def test_views_extract_combines_include():
    def extract(*includes):
        metadatas = []
        for include in includes:
            metadata = MetaData()
            metadata.info["views"] = Views(include=include).are(View("a", "select 1"))
            metadatas.append(metadata)
        return Views.extract(metadatas).include

    assert extract(None, None) is None
    assert extract(["foo.*"], None) == ["foo.*"]
    assert extract(["foo.*"], ["bar.*"]) == ["foo.*", "bar.*"]
