from sqlalchemy import MetaData, text
from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions import Views
from sqlalchemy_declarative_extensions.dialects import check_table_exists
from sqlalchemy_declarative_extensions.view.compare import compare_views


def view_ddl(views: Views):
    def after_create(metadata: MetaData, connection: Connection, **_):
        result = compare_views(connection, views)
        for op in result:
            if check_table_exists(
                connection,
                name=op.view.name,
                schema=op.view.schema or "public",
            ):
                connection.execute(text(f"DROP TABLE {op.view.qualified_name}"))

            connection.execute(op.to_sql(connection.dialect))

    return after_create
