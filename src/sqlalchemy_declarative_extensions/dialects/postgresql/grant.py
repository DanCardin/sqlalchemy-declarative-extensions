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

import itertools
from dataclasses import dataclass, replace
from typing import Generic

from sqlalchemy.sql.elements import TextClause
from sqlalchemy.sql.expression import text

from sqlalchemy_declarative_extensions.dialects.postgresql.grant_type import (
    DefaultGrantTypes,
    G,
    GrantOptions,
    GrantTypes,
)
from sqlalchemy_declarative_extensions.sql import split_schema
from sqlalchemy_declarative_extensions.typing import Protocol, runtime_checkable


@runtime_checkable
class HasName(Protocol):
    name: str


@dataclass(frozen=True)
class Grant(Generic[G]):
    grants: tuple[str | G, ...]
    target_role: str
    grant_option: bool = False
    revoke_: bool = False

    @classmethod
    def new(
        cls,
        grant: str | G,
        *grants: str | G,
        to: str | HasName,
        grant_option=False,
    ) -> Grant:
        return cls(
            grants=tuple(sorted([grant, *grants])),  # type: ignore
            target_role=_coerce_name(to),
            grant_option=grant_option,
        )

    def revoke(self) -> Grant:
        return replace(self, revoke_=True)

    def with_grant_option(self):
        return replace(self, grant_option=True)

    def on_objects(self, *objects: str | HasName, object_type: GrantTypes):
        variants = object_type.to_variants()
        grant = replace(self, grants=tuple(_map_grant_names(variants, *self.grants)))

        names = [_coerce_name(obj) for obj in objects]
        return GrantStatement(grant, grant_type=object_type, targets=tuple(names))

    def on_tables(self, *tables: str | HasName):
        return self.on_objects(*tables, object_type=GrantTypes.table)

    def on_sequences(
        self,
        *sequences: str | HasName,
    ):
        return self.on_objects(*sequences, object_type=GrantTypes.sequence)

    def on_schemas(self, *schemas: str | HasName):
        return self.on_objects(*schemas, object_type=GrantTypes.schema)


@dataclass(frozen=True)
class DefaultGrant:
    grant_type: DefaultGrantTypes
    in_schemas: tuple[str, ...]
    target_role: str | None = None

    @classmethod
    def on_tables_in_schema(
        cls, *in_schemas: str | HasName, for_role: HasName | str | None = None
    ) -> DefaultGrant:
        schemas = _map_schema_names(*in_schemas)
        return cls(
            grant_type=DefaultGrantTypes.table,
            in_schemas=tuple(schemas),
            target_role=_coerce_name(for_role) if for_role is not None else None,
        )

    @classmethod
    def on_sequences_in_schema(
        cls, *in_schemas: str | HasName, for_role: HasName | str | None = None
    ) -> DefaultGrant:
        schemas = _map_schema_names(*in_schemas)
        return cls(
            grant_type=DefaultGrantTypes.sequence,
            in_schemas=tuple(schemas),
            target_role=_coerce_name(for_role) if for_role is not None else None,
        )

    @classmethod
    def on_types_in_schema(
        cls, *in_schemas: str | HasName, for_role: HasName | str | None = None
    ) -> DefaultGrant:
        schemas = _map_schema_names(*in_schemas)
        return cls(
            grant_type=DefaultGrantTypes.type,
            in_schemas=tuple(schemas),
            target_role=_coerce_name(for_role) if for_role is not None else None,
        )

    @classmethod
    def on_functions_in_schema(
        cls, *in_schemas: str | HasName, for_role: HasName | str | None = None
    ) -> DefaultGrant:
        schemas = _map_schema_names(*in_schemas)
        return cls(
            grant_type=DefaultGrantTypes.function,
            in_schemas=tuple(schemas),
            target_role=_coerce_name(for_role) if for_role is not None else None,
        )

    def for_role(self, role: HasName | str):
        return replace(self, target_role=_coerce_name(role))

    def grant(
        self,
        grant: str | G | Grant,
        *grants: str | G,
        to: HasName | str,
        grant_option=False,
    ):
        if not isinstance(grant, Grant):
            grant = Grant(
                grants=tuple(
                    _map_grant_names(self.grant_type.to_variants(), grant, *grants)
                ),
                target_role=_coerce_name(to),
                grant_option=grant_option,
            )
        return DefaultGrantStatement(self, grant)


@dataclass(frozen=True)
class DefaultGrantStatement(Generic[G]):
    default_grant: DefaultGrant
    grant: Grant[G]

    def for_role(self, role: str | HasName) -> DefaultGrantStatement:
        return replace(
            self,
            default_grant=replace(self.default_grant, target_role=_coerce_name(role)),
        )

    def invert(self) -> DefaultGrantStatement:
        return replace(self, grant=replace(self.grant, revoke_=not self.grant.revoke_))

    def to_sql(self) -> TextClause:
        result = []

        result.append("ALTER DEFAULT PRIVILEGES")

        if self.default_grant.target_role:
            result.append(f'FOR ROLE "{self.default_grant.target_role}"')

        schemas_str = ", ".join([f'"{t}"' for t in self.default_grant.in_schemas])
        result.append(f"IN SCHEMA {schemas_str}")

        result.append(_render_grant_or_revoke(self.grant))
        result.append(_render_privilege(self.grant, self.default_grant.grant_type))

        result.append(f"ON {self.default_grant.grant_type.value}S")
        result.append(_render_to_or_from(self.grant))

        text_result = " ".join(result)
        return text(text_result + ";")

    def explode(self):
        return [
            DefaultGrantStatement(
                default_grant=DefaultGrant(
                    grant_type=self.default_grant.grant_type,
                    in_schemas=(schema,),
                    target_role=self.default_grant.target_role,
                ),
                grant=Grant(
                    grants=(grant,),
                    target_role=self.grant.target_role,
                    grant_option=self.grant.grant_option,
                    revoke_=self.grant.revoke_,
                ),
            )
            for schema in self.default_grant.in_schemas
            for grant in self.grant.grants
        ]

    @classmethod
    def combine(cls, grants: list[DefaultGrantStatement]):
        def by_statement(g: DefaultGrantStatement):
            return (
                g.default_grant.grant_type,
                g.default_grant.in_schemas,
                g.default_grant.target_role or "",
                g.grant.target_role,
                g.grant.grant_option,
                g.grant.revoke_,
            )

        result = []
        groups = itertools.groupby(sorted(grants, key=by_statement), key=by_statement)
        for (
            grant_type,
            in_schemas,
            default_target_role,
            target_role,
            grant_option,
            revoke,
        ), group in groups:
            item = cls(
                default_grant=DefaultGrant(
                    grant_type=grant_type,
                    in_schemas=in_schemas,
                    target_role=default_target_role or None,
                ),
                grant=Grant(
                    target_role=target_role,
                    grant_option=grant_option,
                    revoke_=revoke,
                    grants=tuple([g for i in group for g in i.grant.grants]),
                ),
            )
            result.append(item)
        return result


@dataclass(frozen=True)
class GrantStatement(Generic[G]):
    grant: Grant[G]
    grant_type: GrantTypes
    targets: tuple[str, ...]

    def invert(self) -> GrantStatement:
        return replace(self, grant=replace(self.grant, revoke_=not self.grant.revoke_))

    def for_role(self, role: str | HasName) -> GrantStatement:
        return replace(self, grant=replace(self.grant, target_role=_coerce_name(role)))

    def to_sql(self) -> TextClause:
        result = []

        result.append(_render_grant_or_revoke(self.grant))
        result.append(_render_privilege(self.grant, self.grant_type))
        result.append(f"ON {self.grant_type.value}")

        result.append(", ".join([_quote_table_name(t) for t in self.targets]))
        result.append(_render_to_or_from(self.grant))

        grant_option = _render_grant_option(self.grant)
        if grant_option:
            result.append(grant_option)

        text_result = " ".join(result)
        return text(text_result + ";")

    def explode(self):
        return [
            GrantStatement(
                grant=Grant(
                    grants=(grant,),
                    target_role=self.grant.target_role,
                    grant_option=self.grant.grant_option,
                    revoke_=self.grant.revoke_,
                ),
                grant_type=self.grant_type,
                targets=(target,),
            )
            for target in self.targets
            for grant in self.grant.grants
        ]

    @classmethod
    def combine(cls, grants: list[GrantStatement]):
        def by_statement(g: GrantStatement):
            return (
                g.grant_type,
                g.targets,
                g.grant.target_role,
                g.grant.grant_option,
                g.grant.revoke_,
            )

        result = []
        groups = itertools.groupby(sorted(grants, key=by_statement), key=by_statement)
        for (grant_type, targets, target_role, grant_option, revoke), group in groups:
            item = cls(
                grant_type=grant_type,
                targets=targets,
                grant=Grant(
                    target_role=target_role,
                    grant_option=grant_option,
                    revoke_=revoke,
                    grants=tuple([g for i in group for g in i.grant.grants]),
                ),
            )
            result.append(item)
        return result


def _render_grant_or_revoke(grant: Grant) -> str:
    if grant.revoke_:
        return "REVOKE"
    return "GRANT"


def _render_to_or_from(grant: Grant) -> str:
    if grant.revoke_:
        return f'FROM "{grant.target_role}"'
    return f'TO "{grant.target_role}"'


def _quote_table_name(name: str):
    schema, name = split_schema(name)

    if schema:
        return f'"{schema}"."{name}"'
    return f'"{name}"'


def _render_privilege(grant: Grant, grant_type: DefaultGrantTypes | GrantTypes) -> str:
    grant_variant_cls = grant_type.to_variants()
    return ", ".join(v.value for v in grant_variant_cls.from_strings(grant.grants))


def _render_grant_option(grant: Grant) -> str | None:
    if grant.grant_option:
        return "WITH GRANT OPTION"
    return None


def _map_schema_names(*schemas: str | HasName):
    return sorted([_coerce_name(s) for s in schemas])


def _map_grant_names(variant: G, *grants: str | G):
    return sorted(
        [g if isinstance(g, GrantOptions) else variant.from_string(g) for g in grants]
    )


def _coerce_name(name: str | HasName):
    if isinstance(name, HasName):
        return name.name
    return name
