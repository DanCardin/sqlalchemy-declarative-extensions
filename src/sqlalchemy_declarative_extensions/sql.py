from __future__ import annotations


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
