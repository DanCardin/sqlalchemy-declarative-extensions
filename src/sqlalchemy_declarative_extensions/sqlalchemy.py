import sqlalchemy
from sqlalchemy import MetaData, Table
from sqlalchemy.engine import Connection
from typing_extensions import Protocol

version = getattr(sqlalchemy, "__version__", "1.3")


class HasMetaData(Protocol):
    metadata: MetaData


class HasTable(Protocol):
    __table__: Table


def dialect_dispatch(postgresql=None, sqlite=None, mysql=None):
    dispatchers = {
        "postgresql": postgresql,
        "sqlite": sqlite,
        "mysql": mysql,
    }

    def dispatch(connection: Connection, *args, **kwargs):
        dialect_name = connection.dialect.name
        if dialect_name == "pmrsqlite":
            dialect_name = "sqlite"

        dispatcher = dispatchers.get(dialect_name)
        if dispatcher is None:  # pragma: no cover
            raise NotImplementedError(
                f"'{dialect_name}' is not yet supported for this operation."
            )

        return dispatcher(connection, *args, **kwargs)

    return dispatch


if version.startswith("1.3"):
    from sqlalchemy.ext.declarative import (  # type: ignore
        DeclarativeMeta,
        declarative_base,
        instrument_declarative,
    )

    def select(*args):
        return sqlalchemy.select(list(args))

    def create_mapper(cls, metadata):
        return instrument_declarative(cls, {}, metadata)

else:
    from sqlalchemy.orm import DeclarativeMeta, declarative_base, registry

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


__all__ = [
    "create_mapper",
    "declarative_base",
    "DeclarativeMeta",
    "dialect_dispatch",
    "HasMetaData",
    "row_to_dict",
    "select",
]
