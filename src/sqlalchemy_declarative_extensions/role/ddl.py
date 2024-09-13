from __future__ import annotations

from sqlalchemy import MetaData, text
from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions import Roles
from sqlalchemy_declarative_extensions.role.compare import compare_roles
from sqlalchemy_declarative_extensions.sql import match_name


def role_ddl(roles: Roles, role_filter: list[str] | None = None):
    def receive_after_create(metadata: MetaData, connection: Connection, **_):
        result = compare_roles(connection, roles)
        for op in result:
            if not match_name(op.role.name, role_filter):
                continue

            statements = op.to_sql(raw=True)
            if isinstance(statements, list):
                for statement in statements:
                    connection.execute(text(statement))
            else:
                connection.execute(text(statements))

    return receive_after_create
