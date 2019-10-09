from sqlalchemy.engine import Connection


def dialect_dispatch(postgresql=None, sqlite=None):
    dispatchers = {
        "postgresql": postgresql,
        "sqlite": sqlite,
    }

    def dispatch(connection: Connection, **kwargs):
        dialect_name = connection.dialect.name
        if dialect_name == "pmrsqlite":
            dialect_name = "sqlite"

        dispatcher = dispatchers.get(dialect_name)
        if dispatcher is None:
            raise NotImplementedError(
                f"'{dialect_name}' is not yet supported for this operation."
            )

        return dispatcher(connection, **kwargs)

    return dispatch
