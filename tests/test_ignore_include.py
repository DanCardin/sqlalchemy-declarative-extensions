from sqlalchemy import MetaData

from sqlalchemy_declarative_extensions import Procedures
from sqlalchemy_declarative_extensions.function import Function
from sqlalchemy_declarative_extensions.procedure import Procedure
from sqlalchemy_declarative_extensions.sql import filter_ignored
from sqlalchemy_declarative_extensions.trigger import Trigger


def test_filter_ignored_functions_and_procedures():
    functions = [Function("a", "select 1"), Function("b", "select 1", schema="foo")]
    assert [f.name for f in filter_ignored(functions, ["foo.*"])] == ["a"]
    assert [f.name for f in filter_ignored(functions, [], include=["foo.*"])] == ["b"]

    procedures = [Procedure("a", "select 1"), Procedure("b", "select 1", schema="foo")]
    assert [p.name for p in filter_ignored(procedures, ["foo.*"])] == ["a"]
    assert [p.name for p in filter_ignored(procedures, [], include=["foo.*"])] == ["b"]


def test_filter_ignored_with_key():
    triggers = [Trigger("keep", "t", "f"), Trigger("skip_me", "t", "f")]
    kept = filter_ignored(triggers, ["skip_*"], key=lambda t: t.name)
    assert [t.name for t in kept] == ["keep"]


def test_procedures_extract_combines_include():
    a = Procedures(include=["foo.*"], ignore=["a"])
    b = Procedures(include=["bar.*"], ignore=["b"])
    c = Procedures()

    combined = Procedures.extract([_meta(a), _meta(b), _meta(c)])
    assert combined is not None
    assert combined.include == ["foo.*", "bar.*"]
    assert combined.ignore == ["a", "b"]

    assert (
        Procedures.extract([_meta(Procedures()), _meta(Procedures())]).include is None
    )


def _meta(procedures):
    metadata = MetaData()
    metadata.info["procedures"] = procedures
    return metadata
