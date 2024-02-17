from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions.schema import Schemas
from sqlalchemy_declarative_extensions.schema.compare import compare_schemas


def schema_ddl(metadata: MetaData, connection: Connection, **_):
    roles: Schemas | None = metadata.info.get("schemas")
    if not roles:  # pragma: no cover
        return

    result = compare_schemas(connection, roles)
    for op in result:
        statements = op.to_sql()
        connection.execute(statements)
