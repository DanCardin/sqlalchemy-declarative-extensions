import pytest

from sqlalchemy_declarative_extensions.role.base import PGRole
from sqlalchemy_declarative_extensions.role.topological_sort import topological_sort


def test_topological_sort_duplicate():
    with pytest.raises(ValueError) as e:
        topological_sort([PGRole("foo"), PGRole("foo"), PGRole("bar")])
    assert "foo" in str(e.value)
    assert "duplicate" in str(e.value).lower()


def test_topological_sort_cycle_simple():
    with pytest.raises(ValueError) as e:
        topological_sort(
            [
                PGRole("foo", in_roles=["bar"]),
                PGRole("bar", in_roles=["bar"]),
            ]
        )
    assert "bar, foo" in str(e.value)
    assert "cyclical" in str(e.value).lower()


def test_topological_missing_item():
    foo = PGRole("foo", in_roles=["bar"])

    with pytest.raises(ValueError) as e:
        topological_sort([foo])

    assert "bar" in str(e.value)
    assert "missing" in str(e.value).lower()


def test_topological_sort_circle_cycle():
    with pytest.raises(ValueError) as e:
        topological_sort(
            [
                PGRole("foo", in_roles=["bar"]),
                PGRole("bar", in_roles=["bax"]),
                PGRole("bax", in_roles=["baz"]),
                PGRole("baz", in_roles=["foo"]),
            ]
        )
    assert "bar, bax, baz, foo" in str(e.value)
    assert "cyclical" in str(e.value).lower()


def test_topological_sort_no_deps():
    foo = PGRole("foo")
    bar = PGRole("bar")
    result = topological_sort([foo, bar])

    expected_result = [foo, bar]
    assert expected_result == result


def test_topological_sort_simple():
    foo = PGRole("foo", in_roles=["bar"])
    bar = PGRole("bar")
    result = topological_sort([foo, bar])

    expected_result = [bar, foo]
    assert expected_result == result


def test_topological_sort_chain():
    foo = PGRole("foo", in_roles=["bar"])
    bar = PGRole("bar", in_roles=["bax"])
    bax = PGRole("bax", in_roles=["baz"])
    baz = PGRole("baz")
    result = topological_sort([foo, baz, bar, bax])

    expected_result = [baz, bax, bar, foo]
    assert expected_result == result


def test_topological_fork():
    foo = PGRole("foo", in_roles=["bar"])
    bax = PGRole("bax", in_roles=["bar"])
    bar = PGRole("bar", in_roles=["baz"])
    baz = PGRole("baz")
    result = topological_sort([foo, baz, bar, bax])

    expected_result = [baz, bar, foo, bax]
    assert expected_result == result
