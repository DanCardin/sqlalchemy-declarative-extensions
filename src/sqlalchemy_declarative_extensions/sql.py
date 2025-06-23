from __future__ import annotations

import fnmatch
from collections.abc import Sequence

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
