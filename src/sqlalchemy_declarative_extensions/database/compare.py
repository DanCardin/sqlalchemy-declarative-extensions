from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from sqlalchemy.engine.base import Connection

from sqlalchemy_declarative_extensions.database.base import Database, Databases
from sqlalchemy_declarative_extensions.dialects import get_databases
from sqlalchemy_declarative_extensions.op import ExecuteOp
from sqlalchemy_declarative_extensions.role.compare import UseRoleOp
from sqlalchemy_declarative_extensions.role.state import RoleState


@dataclass
class CreateDatabaseOp(ExecuteOp):
    database: Database
    use_role_ops: list[UseRoleOp] | None = None

    @classmethod
    def create_database(cls, operations, database, **kwargs):
        op = cls(Database(database, **kwargs))
        return operations.invoke(op)

    def reverse(self):
        return DropDatabaseOp(self.database)

    def to_sql(self) -> list[str]:
        role_sql = UseRoleOp.to_sql_from_use_role_ops(self.use_role_ops)
        return [*role_sql, self.database.to_sql_create()]


@dataclass
class DropDatabaseOp(ExecuteOp):
    database: Database
    use_role_ops: list[UseRoleOp] | None = None

    @classmethod
    def drop_database(cls, operations, database, **kwargs):
        op = cls(Database(database, **kwargs))
        return operations.invoke(op)

    def reverse(self):
        return CreateDatabaseOp(self.database)

    def to_sql(self) -> list[str]:
        role_sql = UseRoleOp.to_sql_from_use_role_ops(self.use_role_ops)
        return [*role_sql, self.database.to_sql_drop()]


DatabaseOp = Union[CreateDatabaseOp, DropDatabaseOp, UseRoleOp]


def compare_databases(connection: Connection, databases: Databases) -> list[DatabaseOp]:
    existing_databases = get_databases(connection)
    role_state = RoleState.from_connection(connection)

    expected_databases = {s.name: s for s in databases.databases}
    new_databases = expected_databases.keys() - existing_databases.keys()
    removed_databases = existing_databases.keys() - expected_databases.keys()

    result: list[DatabaseOp] = []
    for database_name in sorted(new_databases):
        database = expected_databases[database_name]

        result.append(
            CreateDatabaseOp(database, role_state.use_role(database.use_role))
        )

    if not databases.ignore_unspecified:
        for database_name in sorted(removed_databases, reverse=True):
            database = existing_databases[database_name]

            result.append(
                DropDatabaseOp(database, role_state.use_role(database.use_role))
            )

    result.extend(role_state.reset())

    return result
