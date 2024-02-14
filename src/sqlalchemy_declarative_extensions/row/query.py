from sqlalchemy import MetaData
from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions.row import Rows
from sqlalchemy_declarative_extensions.row.compare import compare_rows


def rows_query(rows: Rows):
    def receive_after_create(metadata: MetaData, connection: Connection, **_):
        results = compare_rows(connection, metadata, rows)
        for result in results:
            result.execute(connection)

    return receive_after_create
