from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions.schema import Schemas
from sqlalchemy_declarative_extensions.schema.compare import compare_schemas
from sqlalchemy_declarative_extensions.sql import match_name


def schema_ddl(schemas: Schemas, schema_filter: list[str] | None = None):
    def receive_after_create(metadata: MetaData, connection: Connection, **_):
        result = compare_schemas(connection, schemas)
        for op in result:
            if not match_name(op.schema.name, schema_filter):
                continue

            statements = op.to_sql()
            connection.execute(statements)

    return receive_after_create
