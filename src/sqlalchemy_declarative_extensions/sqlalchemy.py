from sqlalchemy import MetaData
from sqlalchemy.engine import Connection
from typing_extensions import Protocol


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
