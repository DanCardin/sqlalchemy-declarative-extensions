from __future__ import annotations

import enum
import textwrap
from dataclasses import dataclass, replace

from typing_extensions import Self

from sqlalchemy_declarative_extensions.function import base


@enum.unique
class FunctionSecurity(enum.Enum):
    invoker = "INVOKER"
    definer = "DEFINER"


@enum.unique
class FunctionDataAccess(enum.Enum):
    no_sql = "NO SQL"
    contains_sql = "CONTAINS SQL"
    reads_sql = "READS SQL DATA"
    modifies_sql = "MODIFIES SQL DATA"


@dataclass
class Function(base.Function):
    """Describes a MySQL function."""

    security: FunctionSecurity = FunctionSecurity.definer
    deterministic: bool = False
    data_access: FunctionDataAccess = FunctionDataAccess.contains_sql

    @classmethod
    def from_unknown_function(cls, f: base.Function) -> Self:
        if isinstance(f, cls):
            return f

        return cls(
            name=f.name,
            definition=f.definition,
            language=f.language,
            schema=f.schema,
            returns=f.returns,
            parameters=f.parameters,
        )

    def to_sql_create(self) -> list[str]:
        components = ["CREATE FUNCTION"]

        parameter_str = ""
        if self.parameters:
            parameter_str = ", ".join(self.parameters)

        components.append(f"{self.qualified_name}({parameter_str})")
        components.append(f"RETURNS {self.returns}")

        if self.deterministic:
            components.append("DETERMINISTIC")

        components.append(self.data_access.value)

        if self.security == FunctionSecurity.invoker:
            components.append("SQL SECURITY INVOKER")

        components.append(self.definition)

        return [" ".join(components) + ";"]

    def to_sql_drop(self) -> list[str]:
        return [f"DROP FUNCTION {self.qualified_name};"]

    def with_security(self, security: FunctionSecurity):
        return replace(self, security=security)

    def with_security_definer(self):
        return replace(self, security=FunctionSecurity.definer)

    def with_data_access(self, data_access: FunctionDataAccess):
        return replace(self, data_access=data_access)

    def no_sql(self):
        return self.with_data_access(FunctionDataAccess.no_sql)

    def reads_sql(self):
        return self.with_data_access(FunctionDataAccess.reads_sql)

    def modifies_sql(self):
        return self.with_data_access(FunctionDataAccess.modifies_sql)

    def normalize(self) -> Function:
        definition = textwrap.dedent(self.definition).strip()

        # Remove optional trailing semicolon for comparison robustness
        if definition.endswith(";"):
            definition = definition[:-1]

        returns = self.returns.lower()
        normalized_returns = type_map.get(returns, returns)

        normalized_parameters = None
        if self.parameters:
            normalized_parameters = []
            for param in self.parameters:
                # Naive split, assumes 'name type' format
                parts = param.split(maxsplit=1)
                if len(parts) == 2:
                    name, type_str = parts
                    norm_type = type_map.get(type_str.lower(), type_str.lower())
                    normalized_parameters.append(f"{name} {norm_type}")
                else:
                    normalized_parameters.append(
                        param
                    )  # Keep as is if format unexpected

        return replace(
            self,
            definition=definition,
            returns=normalized_returns,
            parameters=normalized_parameters,
        )


# https://dev.mysql.com/doc/refman/8.4/en/other-vendor-data-types.html
type_map = {
    "boolean": "tinyint",
    "bool": "tinyint",
    "character varying": "varchar",
    "fixed": "decimal",
    "float4": "float",
    "float8": "double",
    "int1": "tinyint",
    "int2": "smallint",
    "int3": "mediumint",
    "int4": "int",
    "integer": "int",
    "int8": "bigint",
    "long varbinary": "mediumblob",
    "long varchar": "mediumtext",
    "long": "mediumtext",
    "middleint": "mediumint",
    "numeric": "decimal",
}
