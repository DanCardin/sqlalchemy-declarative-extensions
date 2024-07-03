from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions.row import Rows
from sqlalchemy_declarative_extensions.row.compare import compare_rows


def rows_query(rows: Rows, row_filter: list[str] | None = None):
    def receive_after_create(metadata: MetaData, connection: Connection, **_):
        results = compare_rows(connection, metadata, rows, row_filter)
        for op in results:
            op.execute(connection)

    return receive_after_create
