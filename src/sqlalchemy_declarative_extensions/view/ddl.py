from __future__ import annotations

from sqlalchemy import MetaData, text
from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions import Views
from sqlalchemy_declarative_extensions.sql import match_name
from sqlalchemy_declarative_extensions.view.compare import compare_views


def view_ddl(views: Views, view_filter: list[str] | None = None):
    def after_create(metadata: MetaData, connection: Connection, **_):
        result = compare_views(connection, views, normalize_with_connection=False)
        for op in result:
            if not match_name(op.view.qualified_name, view_filter):
                continue

            for command in op.to_sql(connection.dialect):
                connection.execute(text(command))

    return after_create
