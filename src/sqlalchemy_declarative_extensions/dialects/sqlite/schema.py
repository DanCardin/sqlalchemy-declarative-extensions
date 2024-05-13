from typing import Optional

from sqlalchemy import bindparam, text


def views_query(schema: Optional[str] = None):
    tablename = "sqlite_master"
    if schema:
        tablename = f"{schema}.{tablename}"

    return text(
        "SELECT"  # noqa: S608
        " :schema AS schema,"
        " name AS name,"
        " sql AS definition,"
        " false as materialized"
        f" FROM {tablename}"
        " WHERE type == 'view'",
    ).bindparams(bindparam("schema", schema))
