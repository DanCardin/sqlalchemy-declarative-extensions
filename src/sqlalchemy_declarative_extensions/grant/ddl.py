from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions.grant.base import Grants
from sqlalchemy_declarative_extensions.grant.compare import compare_grants
from sqlalchemy_declarative_extensions.role.base import Roles


def grant_ddl(grants: Grants, roles: Roles | None = None):
    def receive_event(metadata: MetaData, connection: Connection, **_):
        result = compare_grants(connection, grants, roles=roles)
        for op in result:
            connection.execute(op.to_sql())

    return receive_event
