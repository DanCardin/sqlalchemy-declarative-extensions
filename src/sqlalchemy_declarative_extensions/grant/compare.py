from __future__ import annotations

from dataclasses import dataclass
from typing import List, Union

from sqlalchemy import text
from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions.dialect.postgresql import default_acl_query
from sqlalchemy_declarative_extensions.grant.base import Grants
from sqlalchemy_declarative_extensions.grant.postgresql.base import (
    DefaultGrantStatement,
)
from sqlalchemy_declarative_extensions.sqlalchemy import dialect_dispatch


@dataclass
class GrantPrivilegesOp:
    grant: DefaultGrantStatement

    @classmethod
    def grant_privileges(cls, operations, grant):
        op = cls(grant)
        return operations.invoke(op)

    def reverse(self):
        return RevokePrivilegesOp(self.grant)


@dataclass
class RevokePrivilegesOp:
    grant: DefaultGrantStatement

    @classmethod
    def revoke_privileges(cls, operations, grant):
        op = cls(grant)
        return operations.invoke(op)

    def reverse(self):
        return GrantPrivilegesOp(self.grant)


Operation = Union[GrantPrivilegesOp, RevokePrivilegesOp]


def compare_grants(connection: Connection, grants: Grants) -> List[Operation]:
    result: List[Operation] = []
    if not grants:
        return result

    existing_default_grants = get_default_grants(connection)

    missing_grants = set(grants) - set(existing_default_grants)
    extra_grants = set(existing_default_grants) - set(grants)

    for missing_grant in missing_grants:
        result.append(GrantPrivilegesOp(missing_grant))

    if not grants.ignore_unspecified:
        for extra_grant in extra_grants:
            result.append(RevokePrivilegesOp(extra_grant))

    return result


def get_default_grants_postgresql(connection: Connection):
    from sqlalchemy_declarative_extensions.grant.postgresql.parse import parse_acl

    default_permissions = connection.execute(default_acl_query).fetchall()

    result = []
    for permission in default_permissions:
        for acl_item in permission.acl:
            grant_permissions = parse_acl(
                acl_item,
                permission.object_type,
                permission.schema_name,
            )
            result.extend(grant_permissions)
    return result


get_default_grants = dialect_dispatch(
    postgresql=get_default_grants_postgresql,
)
