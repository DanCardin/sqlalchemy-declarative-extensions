from typing import Optional

from sqlalchemy import MetaData, text
from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions.grant.base import Grants
from sqlalchemy_declarative_extensions.grant.compare import compare_grants
from sqlalchemy_declarative_extensions.role.base import Roles


def grant_ddl(grants: Grants, after: bool):
    def receive_event(metadata: MetaData, connection: Connection, **_):
        roles: Optional[Roles] = metadata.info.get("roles")
        result = compare_grants(connection, grants, roles=roles)
        for op in result:
            for statement in op.to_sql():
                connection.execute(text(statement))

    return receive_event
