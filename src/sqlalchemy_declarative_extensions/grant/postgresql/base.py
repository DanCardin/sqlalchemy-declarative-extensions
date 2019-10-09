"""Abstract a postgresql GRANT statement.

See https://www.postgresql.org/docs/latest/sql-grant.html.

ALTER DEFAULT PRIVILEGES
    [ FOR { ROLE | USER } target_role [, ...] ]
    [ IN SCHEMA schema_name [, ...] ]
    abbreviated_grant_or_revoke

where abbreviated_grant_or_revoke is one of:

GRANT { { SELECT | INSERT | UPDATE | DELETE | TRUNCATE | REFERENCES | TRIGGER }
    [, ...] | ALL [ PRIVILEGES ] }
    ON TABLES
    TO { [ GROUP ] role_name | PUBLIC } [, ...] [ WITH GRANT OPTION ]

GRANT { { USAGE | SELECT | UPDATE }
    [, ...] | ALL [ PRIVILEGES ] }
    ON SEQUENCES
    TO { [ GROUP ] role_name | PUBLIC } [, ...] [ WITH GRANT OPTION ]

GRANT { EXECUTE | ALL [ PRIVILEGES ] }
    ON FUNCTIONS
    TO { [ GROUP ] role_name | PUBLIC } [, ...] [ WITH GRANT OPTION ]

GRANT { USAGE | ALL [ PRIVILEGES ] }
    ON TYPES
    TO { [ GROUP ] role_name | PUBLIC } [, ...] [ WITH GRANT OPTION ]
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Generic, Optional, Tuple, Union

from sqlalchemy.sql.elements import TextClause
from sqlalchemy.sql.expression import text

from sqlalchemy_declarative_extensions.grant.postgresql.grant_type import (
    DefaultGrantTypes,
    G,
    GrantTypes,
)
from sqlalchemy_declarative_extensions.role.base import Role
from sqlalchemy_declarative_extensions.schema.base import Schema


@dataclass(frozen=True)
class Grant(Generic[G]):
    target_role: str

    grants: Tuple[G, ...] = field(default_factory=tuple)
    grant_option: bool = False
    revoke_: bool = False
    grantor: Optional[str] = None

    @classmethod
    def for_role(cls, role: Union[str, Role]) -> Grant:
        role_name = role.name if isinstance(role, Role) else role
        return cls(role_name)

    def grant(self, grant: str, *grants: str) -> Grant:
        return replace(self, grants=tuple([grant, *grants]))

    def revoke(self, grant: str, *grants: str) -> Grant:
        return replace(self, grants=tuple([grant, *grants]), revoke_=True)

    def with_grant_option(self):
        return replace(self, grant_option=True)

    def granted_by(self, grantor: str):
        return replace(self, grantor=grantor)

    def default(self):
        return DefaultGrantOption(self)

    def on_table(self, *tables: str):
        return GrantStatement(self, grant_type=GrantTypes.table, targets=tuple(tables))

    def in_schema(self, *schemas: Union[str, Schema]):
        schema_names = [s.name if isinstance(s, Schema) else s for s in schemas]
        return GrantStatement(
            self, grant_type=GrantTypes.schema, targets=tuple(schema_names)
        )

    def _render_grant_or_revoke(self) -> str:
        if self.revoke_:
            return "REVOKE"
        return "GRANT"

    def _render_to_or_from(self, role: str) -> str:
        if self.revoke_:
            return f"FROM {role}"
        return f"TO {role}"

    def _render_privilege(
        self, grant_type: Union[DefaultGrantTypes, GrantTypes]
    ) -> str:
        grant_variant_cls = grant_type.to_variants()
        return ", ".join(v.value for v in grant_variant_cls.from_strings(self.grants))

    def _render_grant_option(self) -> Optional[str]:
        if self.grant_option:
            return "WITH GRANT OPTION"
        return None


@dataclass(frozen=True)
class DefaultGrantOption:
    privileges: Grant

    def _schema_names(self, *schemas: Union[str, Schema]):
        return [s.name if isinstance(s, Schema) else s for s in schemas]

    def on_tables_in_schema(
        self, *in_schemas: Union[str, Schema], for_role: Optional[Role] = None
    ) -> DefaultGrantStatement:
        schemas = self._schema_names(*in_schemas)
        return DefaultGrantStatement(
            self.privileges,
            grant_type=DefaultGrantTypes.table,
            in_schemas=tuple(schemas),
            for_role=for_role.name if isinstance(for_role, Role) else for_role,
        )

    def on_sequences_in_schema(
        self, *in_schemas: Union[str, Schema], for_role: Optional[Role] = None
    ) -> DefaultGrantStatement:
        schemas = self._schema_names(*in_schemas)
        return DefaultGrantStatement(
            self.privileges,
            grant_type=DefaultGrantTypes.sequence,
            in_schemas=tuple(schemas),
            for_role=for_role.name if isinstance(for_role, Role) else for_role,
        )

    def on_types_in_schema(
        self, *in_schemas: Union[str, Schema], for_role: Optional[Role] = None
    ) -> DefaultGrantStatement:
        schemas = self._schema_names(*in_schemas)
        return DefaultGrantStatement(
            self.privileges,
            grant_type=DefaultGrantTypes.type,
            in_schemas=tuple(schemas),
            for_role=for_role.name if isinstance(for_role, Role) else for_role,
        )

    def on_functions_in_schema(
        self, *in_schemas: Union[str, Schema], for_role: Optional[Role] = None
    ) -> DefaultGrantStatement:
        schemas = self._schema_names(*in_schemas)
        return DefaultGrantStatement(
            self.privileges,
            grant_type=DefaultGrantTypes.function,
            in_schemas=tuple(schemas),
            for_role=for_role.name if isinstance(for_role, Role) else for_role,
        )


@dataclass(frozen=True)
class DefaultGrantStatement(Generic[G]):
    privileges: Grant[G]
    grant_type: DefaultGrantTypes
    in_schemas: Tuple[str, ...]
    for_role: Optional[str]

    def to_sql(self) -> TextClause:
        result = []

        result.append("ALTER DEFAULT PRIVILEGES")

        if self.for_role:
            result.append(f"FOR ROLE {self.for_role}")

        schemas_str = ", ".join(self.in_schemas)
        result.append(f"IN SCHEMA {schemas_str}")

        result.append(self.privileges._render_grant_or_revoke())
        result.append(self.privileges._render_privilege(self.grant_type))

        result.append(f"ON {self.grant_type.value}S")
        result.append(self.privileges._render_to_or_from(self.privileges.target_role))

        text_result = " ".join(result)
        return text(text_result)


@dataclass(frozen=True)
class GrantStatement(Generic[G]):
    privileges: Grant[G]
    grant_type: GrantTypes
    targets: Tuple[str, ...]

    def to_sql(self) -> TextClause:
        result = []

        result.append(self.privileges._render_grant_or_revoke())
        result.append(self.privileges._render_privilege(self.grant_type))
        result.append(f"ON {self.grant_type.value}")

        result.append(", ".join(self.targets))
        result.append(self.privileges._render_to_or_from(self.privileges.target_role))

        grant_option = self.privileges._render_grant_option()
        if grant_option:
            result.append(grant_option)

        text_result = " ".join(result)
        return text(text_result)
