from __future__ import annotations

from sqlalchemy_declarative_extensions.typing import Protocol, runtime_checkable


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


@runtime_checkable
class HasName(Protocol):
    name: str


def coerce_name(name: str | HasName):
    if isinstance(name, HasName):
        return name.name
    return name
