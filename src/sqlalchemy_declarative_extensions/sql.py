from __future__ import annotations

import fnmatch
from collections.abc import Callable, Iterable, Sequence
from operator import attrgetter
from typing import Any, TypeVar

from sqlalchemy_declarative_extensions.typing import Protocol, runtime_checkable


def qualify_name(schema: str | None, name: str, quote=False) -> str:
    if not schema or schema == "public":
        if quote:
            return f'"{name}"'
        return name

    result = f"{schema}.{name}"
    if quote:
        return quote_name(result)
    return result


def split_schema(
    tablename: str, *, schema: str | None = None
) -> tuple[str | None, str]:
    try:
        schema, table = tablename.split(".", 1)
    except ValueError:
        table = tablename
    return schema, table


def match_name(name: str, globs: Sequence[str] | None) -> bool:
    if globs is None:
        return True

    for glob in globs:
        if fnmatch.fnmatch(name, glob):
            return True
    return False


T = TypeVar("T")


def is_ignored(
    name: str,
    ignore: Iterable[str],
    *,
    include: Iterable[str] | None = None,
    case_sensitive: bool = True,
) -> bool:
    """Return whether `name` is excluded from comparison.

    That is the case if it matches any of the `ignore` globs, or if `include` is set
    and it matches none of those globs.
    """
    if not case_sensitive:
        name = name.lower()
        ignore = [pattern.lower() for pattern in ignore]
        include = None if include is None else [p.lower() for p in include]

    if include is not None and not any(fnmatch.fnmatch(name, p) for p in include):
        return True

    return any(fnmatch.fnmatch(name, pattern) for pattern in ignore)


def filter_ignored(
    items: Iterable[T],
    ignore: Iterable[str],
    *,
    include: Iterable[str] | None = None,
    case_sensitive: bool = True,
    key: Callable[[Any], str] = attrgetter("qualified_name"),
) -> list[T]:
    """Drop the items whose `key` (by default, `qualified_name`) is excluded.

    See `is_ignored` for how `ignore` and `include` globs are interpreted.
    """
    ignore = list(ignore)
    include = None if include is None else list(include)
    return [
        item
        for item in items
        if not is_ignored(
            key(item), ignore, include=include, case_sensitive=case_sensitive
        )
    ]


@runtime_checkable
class HasName(Protocol):
    name: str


def coerce_name(name: str | HasName):
    if isinstance(name, HasName):
        return name.name
    return name


def quote_name(name: str) -> str:
    components = [f'"{component}"' for component in name.split(".")]
    return ".".join(components)
