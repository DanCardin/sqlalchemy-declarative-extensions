from __future__ import annotations

from sqlalchemy import MetaData, text
from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions import Procedures
from sqlalchemy_declarative_extensions.procedure.compare import compare_procedures
from sqlalchemy_declarative_extensions.sql import match_name


def procedure_ddl(procedures: Procedures, procedure_filter: list[str] | None = None):
    def after_create(metadata: MetaData, connection: Connection, **_):
        result = compare_procedures(connection, procedures, metadata)
        for op in result:
            if not match_name(op.procedure.qualified_name, procedure_filter):
                continue

            command = op.to_sql()
            connection.execute(text(command))

    return after_create
