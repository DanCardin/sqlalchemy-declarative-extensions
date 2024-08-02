"""Abstract a snowflake GRANT statement."""

from __future__ import annotations

import itertools
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Generic, Sequence

from typing_extensions import Self

from sqlalchemy_declarative_extensions.context import context
from sqlalchemy_declarative_extensions.dialects.snowflake.grant_type import (
    DefaultGrantTypes,
    G,
    GrantOptions,
    GrantTypes,
)
from sqlalchemy_declarative_extensions.grant import base
from sqlalchemy_declarative_extensions.sql import HasName, coerce_name

if TYPE_CHECKING:
    from sqlalchemy_declarative_extensions.role import Role


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
            target_role=coerce_name(to),
            grant_option=grant_option,
        )

    def revoke(self) -> Grant:
        return replace(self, revoke_=True)

    def with_grant_option(self):
        return replace(self, grant_option=True)

    def on_objects(self, *objects: str | HasName, object_type: GrantTypes):
        variants = object_type.to_variants()
        grant = replace(self, grants=tuple(_map_grant_names(variants, *self.grants)))

        names = [coerce_name(obj) for obj in objects]
        return GrantStatement(
            grant,
            grant_type=object_type,
            targets=tuple(names),
            use_role=coerce_name(context.role) if context.role else None,
        )

    def on_databases(self, *databases: str | HasName):
        return self.on_objects(*databases, object_type=GrantTypes.database)

    def on_warehouses(self, *warehouses: str | HasName):
        return self.on_objects(*warehouses, object_type=GrantTypes.warehouse)

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
    in_databases: tuple[str, ...] = ()
    in_schemas: tuple[str, ...] = ()
    target_role: str | None = None

    @classmethod
    def _on_kind_in_database(
        cls,
        grant_type: DefaultGrantTypes,
        in_databases: tuple[str | HasName, ...],
        for_role: HasName | None = None,
    ) -> Self:
        databases = base.map_schema_names(*in_databases)
        return cls(
            grant_type=grant_type,
            in_databases=tuple(databases),
            target_role=coerce_name(for_role) if for_role is not None else None,
        )

    @classmethod
    def on_schemas_in_database(
        cls, *databases: str | HasName, for_role: HasName | None = None
    ) -> Self:
        return cls._on_kind_in_database(DefaultGrantTypes.schema, databases, for_role)

    @classmethod
    def on_tables_in_database(
        cls, *databases: str | HasName, for_role: HasName | None = None
    ) -> Self:
        return cls._on_kind_in_database(DefaultGrantTypes.table, databases, for_role)

    @classmethod
    def on_sequences_in_database(
        cls, *databases: str | HasName, for_role: HasName | None = None
    ) -> Self:
        return cls._on_kind_in_database(DefaultGrantTypes.sequence, databases, for_role)

    @classmethod
    def on_types_in_schema(
        cls, *databases: str | HasName, for_role: HasName | None = None
    ) -> Self:
        return cls._on_kind_in_database(DefaultGrantTypes.type, databases, for_role)

    @classmethod
    def on_functions_in_database(
        cls, *databases: str | HasName, for_role: HasName | None = None
    ) -> Self:
        return cls._on_kind_in_database(DefaultGrantTypes.function, databases, for_role)

    @classmethod
    def on_procedures_in_database(
        cls, *databases: str | HasName, for_role: HasName | None = None
    ) -> Self:
        return cls._on_kind_in_database(
            DefaultGrantTypes.procedure, databases, for_role
        )

    @classmethod
    def on_tasks_in_database(
        cls, *databases: str | HasName, for_role: HasName | None = None
    ) -> Self:
        return cls._on_kind_in_database(DefaultGrantTypes.task, databases, for_role)

    @classmethod
    def on_views_in_database(
        cls, *databases: str | HasName, for_role: HasName | None = None
    ) -> Self:
        return cls._on_kind_in_database(DefaultGrantTypes.view, databases, for_role)

    @classmethod
    def on_stages_in_database(
        cls, *databases: str | HasName, for_role: HasName | None = None
    ) -> Self:
        return cls._on_kind_in_database(DefaultGrantTypes.stage, databases, for_role)

    @classmethod
    def on_file_formats_in_database(
        cls, *databases: str | HasName, for_role: HasName | None = None
    ) -> Self:
        return cls._on_kind_in_database(
            DefaultGrantTypes.file_format, databases, for_role
        )

    @classmethod
    def on_streams_in_database(
        cls, *databases: str | HasName, for_role: HasName | None = None
    ) -> Self:
        return cls._on_kind_in_database(DefaultGrantTypes.stream, databases, for_role)

    def for_role(self, role: Role | str):
        return replace(self, target_role=coerce_name(role))

    def grant(
        self,
        grant: str | G | Grant,
        *grants: str | G,
        to,
        grant_option=False,
    ):
        if not isinstance(grant, Grant):
            grant = Grant(
                grants=tuple(
                    _map_grant_names(self.grant_type.to_variants(), grant, *grants)
                ),
                target_role=coerce_name(to),
                grant_option=grant_option,
            )
        return DefaultGrantStatement(
            self, grant, use_role=coerce_name(context.role) if context.role else None
        )


@dataclass(frozen=True)
class DefaultGrantStatement(base.DefaultGrantStatement, Generic[G]):
    default_grant: DefaultGrant
    grant: Grant[G]
    use_role: Role | str | None = None

    def for_role(self, role: str | HasName) -> DefaultGrantStatement:
        return replace(
            self,
            default_grant=replace(self.default_grant, target_role=coerce_name(role)),
        )

    def invert(self) -> DefaultGrantStatement:
        return replace(self, grant=replace(self.grant, revoke_=not self.grant.revoke_))

    def to_sql(self) -> list[str]:
        result = []

        result.append(base.render_grant_or_revoke(self.grant.revoke_))
        result.append(_render_privilege(self.grant, self.default_grant.grant_type))
        result.append(f"ON FUTURE {self.default_grant.grant_type.value}S")

        in_databases = self.default_grant.in_databases
        in_schemas = self.default_grant.in_schemas
        assert (in_databases or in_schemas) and not (in_databases and in_schemas)

        if in_databases:
            schemas_str = ", ".join([f'"{t}"' for t in in_databases])
            result.append(f"IN DATABASE {schemas_str}")

        if in_schemas:
            schemas_str = ", ".join([f'"{t}"' for t in in_schemas])
            result.append(f"IN SCHEMA {schemas_str}")

        result.append(
            base.render_to_or_from(self.grant.revoke_, self.grant.target_role)
        )

        grant_option = base.render_grant_option(self.grant.grant_option)
        if grant_option:
            result.append(grant_option)

        text_result = " ".join(result) + ";"
        return [text_result]

    def explode(self):
        # TODO: Also do in_schemas, also disallow in_schemas and in_databases at the same time
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
                use_role=self.use_role,
            )
            for schema in self.default_grant.in_databases
            for grant in self.grant.grants
        ]

    @classmethod
    def combine(cls, grants: Sequence[Self]) -> list[Self]:
        def by_statement(g: DefaultGrantStatement):
            return (
                g.default_grant.grant_type,
                g.default_grant.in_schemas,
                g.default_grant.target_role or "",
                g.grant.target_role,
                g.grant.grant_option,
                g.grant.revoke_,
                g.use_role,
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
            use_role,
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
                use_role=use_role,
            )
            result.append(item)
        return result


@dataclass(frozen=True)
class GrantStatement(base.GrantStatement, Generic[G]):
    grant: Grant[G]
    grant_type: GrantTypes
    targets: tuple[str, ...]
    use_role: Role | str | None = None

    def invert(self) -> GrantStatement:
        return replace(self, grant=replace(self.grant, revoke_=not self.grant.revoke_))

    def for_role(self, role: str | HasName) -> GrantStatement:
        return replace(self, grant=replace(self.grant, target_role=coerce_name(role)))

    def to_sql(self) -> list[str]:
        result = []

        result.append(base.render_grant_or_revoke(self.grant.revoke_))
        result.append(_render_privilege(self.grant, self.grant_type))
        result.append(f"ON {self.grant_type.value}")

        result.append(", ".join([base.quote_table_name(t) for t in self.targets]))
        result.append(
            base.render_to_or_from(self.grant.revoke_, self.grant.target_role)
        )

        grant_option = base.render_grant_option(self.grant.grant_option)
        if grant_option:
            result.append(grant_option)

        text_result = " ".join(result) + ";"
        return [text_result]

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
                use_role=self.use_role,
            )
            for target in self.targets
            for grant in self.grant.grants
        ]

    @classmethod
    def combine(cls, grants: Sequence[Self]) -> list[Self]:
        def by_statement(g: Self):
            return (
                g.grant_type,
                g.targets,
                g.grant.target_role,
                g.grant.grant_option,
                g.grant.revoke_,
                g.use_role,
            )

        result = []
        groups = itertools.groupby(sorted(grants, key=by_statement), key=by_statement)
        for (
            grant_type,
            targets,
            target_role,
            grant_option,
            revoke,
            use_role,
        ), group in groups:
            item = cls(
                grant_type=grant_type,
                targets=targets,
                grant=Grant(
                    target_role=target_role,
                    grant_option=grant_option,
                    revoke_=revoke,
                    grants=tuple([g for i in group for g in i.grant.grants]),
                ),
                use_role=use_role,
            )
            result.append(item)
        return result


def _render_privilege(grant: Grant, grant_type: DefaultGrantTypes | GrantTypes) -> str:
    grant_variant_cls = grant_type.to_variants()
    return ", ".join(v.value for v in grant_variant_cls.from_strings(grant.grants))


def _map_grant_names(variant: G, *grants: str | G):
    return sorted(
        [g if isinstance(g, GrantOptions) else variant.from_string(g) for g in grants]
    )
