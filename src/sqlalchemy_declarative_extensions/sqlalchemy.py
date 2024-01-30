import sqlalchemy
from sqlalchemy import MetaData
from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions.typing import Protocol

version = getattr(sqlalchemy, "__version__", "1.3")


class HasMetaData(Protocol):
    metadata: MetaData


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


def escape_params(query: str) -> str:
    return query.replace(":", r"\:")


if version.startswith("1.3"):
    from sqlalchemy.ext.declarative import DeclarativeMeta, instrument_declarative

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
