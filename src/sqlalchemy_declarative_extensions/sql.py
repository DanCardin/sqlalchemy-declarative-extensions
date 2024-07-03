from __future__ import annotations

import fnmatch
from collections.abc import Sequence


def qualify_name(schema: str | None, name: str, quote=False) -> str:
    if not schema or schema == "public":
        if quote:
            return f'"{name}"'
        return name

    if quote:
        return f'"{schema}"."{name}"'
    return f"{schema}.{name}"


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
