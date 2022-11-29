import pytest

from sqlalchemy_declarative_extensions.role.generic import Role
from sqlalchemy_declarative_extensions.role.topological_sort import topological_sort


def test_topological_sort_duplicate():
    with pytest.raises(ValueError) as e:
        topological_sort([Role("foo"), Role("foo"), Role("bar")])
    assert "foo" in str(e.value)
    assert "duplicate" in str(e.value).lower()


def test_topological_sort_cycle_simple():
    with pytest.raises(ValueError) as e:
        topological_sort(
            [
                Role("foo", in_roles=["bar"]),
                Role("bar", in_roles=["bar"]),
            ]
        )
    assert "bar, foo" in str(e.value)
    assert "cyclical" in str(e.value).lower()


def test_topological_missing_item():
    foo = Role("foo", in_roles=["bar"])

    with pytest.raises(ValueError) as e:
        topological_sort([foo])

    assert "bar" in str(e.value)
    assert "missing" in str(e.value).lower()


def test_topological_sort_circle_cycle():
    with pytest.raises(ValueError) as e:
        topological_sort(
            [
                Role("foo", in_roles=["bar"]),
                Role("bar", in_roles=["bax"]),
                Role("bax", in_roles=["baz"]),
                Role("baz", in_roles=["foo"]),
            ]
        )
    assert "bar, bax, baz, foo" in str(e.value)
    assert "cyclical" in str(e.value).lower()


def test_topological_sort_no_deps():
    foo = Role("foo")
    bar = Role("bar")
    result = topological_sort([foo, bar])

    expected_result = [foo, bar]
    assert expected_result == result


def test_topological_sort_simple():
    foo = Role("foo", in_roles=["bar"])
    bar = Role("bar")
    result = topological_sort([foo, bar])

    expected_result = [bar, foo]
    assert expected_result == result


def test_topological_sort_chain():
    foo = Role("foo", in_roles=["bar"])
    bar = Role("bar", in_roles=["bax"])
    bax = Role("bax", in_roles=["baz"])
    baz = Role("baz")
    result = topological_sort([foo, baz, bar, bax])

    expected_result = [baz, bax, bar, foo]
    assert expected_result == result


def test_topological_fork():
    foo = Role("foo", in_roles=["bar"])
    bax = Role("bax", in_roles=["bar"])
    bar = Role("bar", in_roles=["baz"])
    baz = Role("baz")
    result = topological_sort([foo, baz, bar, bax])

    expected_result = [baz, bar, foo, bax]
    assert expected_result == result
