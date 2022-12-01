from typing import Optional

from sqlalchemy import MetaData
from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions import Roles
from sqlalchemy_declarative_extensions.role.compare import compare_roles


def role_ddl(metadata: MetaData, connection: Connection, **_):
    roles: Optional[Roles] = metadata.info.get("roles")
    if not roles:  # pragma: no cover
        return

    result = compare_roles(connection, roles)
    for op in result:
        connection.execute(op.to_sql())
