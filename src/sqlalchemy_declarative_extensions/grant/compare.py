from __future__ import annotations

from dataclasses import dataclass
from typing import List, Union

from sqlalchemy import text
from sqlalchemy.engine import Connection

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

    default_permissions_query = text(
        """
        SELECT
            pg_authid.rolname as role_name,
            pg_namespace.nspname as schema_name,
            pg_default_acl.defaclobjtype as object_type,
            pg_default_acl.defaclacl as acl
        FROM pg_default_acl
        JOIN pg_authid ON pg_default_acl.defaclrole = pg_authid.oid
        JOIN pg_namespace ON pg_default_acl.defaclnamespace = pg_namespace.oid
    """
    )

    default_permissions = connection.execute(default_permissions_query).fetchall()

    result = []
    for permission in default_permissions:
        grant_permissions = parse_acl(permission.acl, permission.object_type)
        result.extend(grant_permissions)
    return result


get_default_grants = dialect_dispatch(
    postgresql=get_default_grants_postgresql,
)
