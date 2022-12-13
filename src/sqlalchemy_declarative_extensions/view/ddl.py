from sqlalchemy import MetaData
from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions import Views
from sqlalchemy_declarative_extensions.view.compare import compare_views


def view_ddl(views: Views):
    def after_create(metadata: MetaData, connection: Connection, **_):
        result = compare_views(connection, views)
        for op in result:
            connection.execute(op.to_sql(connection.dialect))

    return after_create
