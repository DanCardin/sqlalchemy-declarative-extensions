from sqlalchemy import MetaData, text
from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions import Views
from sqlalchemy_declarative_extensions.view.compare import compare_views


def view_ddl(views: Views):
    def after_create(metadata: MetaData, connection: Connection, **_):
        result = compare_views(
            connection, views, metadata, normalize_with_connection=False
        )
        for op in result:
            for command in op.to_sql(connection.dialect):
                connection.execute(text(command))

    return after_create
