from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions.grant.base import Grants
from sqlalchemy_declarative_extensions.grant.postgresql.base import (
    DefaultGrantStatement,
)


def grant_ddl(grants: Grants, default: bool):
    def receive_event(_target, connection: Connection, **_):
        for grant in grants:
            is_default_grant = isinstance(grant, DefaultGrantStatement)
            if default and is_default_grant or not default and not is_default_grant:
                connection.execute(grant.to_sql())

    return receive_event
