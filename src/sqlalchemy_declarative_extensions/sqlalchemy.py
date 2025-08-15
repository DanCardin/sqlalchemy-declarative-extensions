from __future__ import annotations

import re
from typing import Callable, TypeVar

import sqlalchemy
from sqlalchemy import MetaData
from sqlalchemy.engine import Connection
from typing_extensions import Concatenate, ParamSpec

from sqlalchemy_declarative_extensions.typing import Protocol

version = getattr(sqlalchemy, "__version__", "1.3")


class HasMetaData(Protocol):
    metadata: MetaData


T = TypeVar("T")
P = ParamSpec("P")


def dialect_dispatch(
    postgresql: Callable[Concatenate[Connection, P], T] | None = None,
    sqlite: Callable[Concatenate[Connection, P], T] | None = None,
    mysql: Callable[Concatenate[Connection, P], T] | None = None,
    snowflake: Callable[Concatenate[Connection, P], T] | None = None,
    default: Callable[Concatenate[Connection, P], T] | None = None,
) -> Callable[Concatenate[Connection, P], T]:
    dispatchers = {
        "postgresql": postgresql,
        "sqlite": sqlite,
        "mysql": mysql,
        "snowflake": snowflake,
    }

    def dispatch(connection: Connection, *args: P.args, **kwargs: P.kwargs) -> T:
        dialect_name = connection.dialect.name
        if "sqlite" in dialect_name:
            dialect_name = "sqlite"

        dispatcher = dispatchers.get(dialect_name) or default
        if dispatcher is None:  # pragma: no cover
            raise NotImplementedError(
                f"'{dialect_name}' is not yet supported for this operation."
            )

        return dispatcher(connection, *args, **kwargs)

    return dispatch


# https://github.com/sqlalchemy/sqlalchemy/blob/2e9902a34fafff0ac6d6c521a86c7dea3d96a392/lib/sqlalchemy/sql/elements.py#L2334
_sqlalchemy_bind_params_regex = re.compile(r"(?<![:\w\x5c]):(\w+)(?!:)", re.UNICODE)


def escape_params(query: str) -> str:
    return _sqlalchemy_bind_params_regex.sub(r"\\:\1", query)


if version.startswith("1.3"):
    from sqlalchemy.ext.declarative import (  # type: ignore  # type: ignore
        DeclarativeMeta,
        instrument_declarative,
    )

    def select(*args):
        return sqlalchemy.select(list(args))

    def create_mapper(cls, metadata):
        return instrument_declarative(cls, {}, metadata)

else:
    from sqlalchemy.orm import DeclarativeMeta, registry

    select = sqlalchemy.select

    def create_mapper(cls, metadata):
        reg = registry(metadata=metadata)
        return reg.mapped(cls)


if version.startswith(("1.4", "2")):

    def row_to_dict(row):
        return row._asdict()

else:

    def row_to_dict(row):
        return dict(row)


def declarative_base() -> HasMetaData:
    if version.startswith("2"):
        from sqlalchemy.orm import DeclarativeBase

        return DeclarativeBase

    if version.startswith("1.3"):
        from sqlalchemy.ext.declarative import declarative_base
    else:
        from sqlalchemy.orm import declarative_base

    return declarative_base()


__all__ = [
    "create_mapper",
    "declarative_base",
    "DeclarativeMeta",
    "dialect_dispatch",
    "HasMetaData",
    "row_to_dict",
    "select",
]
