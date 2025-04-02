from __future__ import annotations

import enum
import textwrap
from dataclasses import dataclass, replace
from typing import List, Optional

from sqlalchemy_declarative_extensions.function import base
from sqlalchemy_declarative_extensions.sql import quote_name


@enum.unique
class FunctionSecurity(enum.Enum):
    invoker = "INVOKER"
    definer = "DEFINER"


@enum.unique
class FunctionVolatility(enum.Enum):
    VOLATILE = "VOLATILE"
    STABLE = "STABLE"
    IMMUTABLE = "IMMUTABLE"

    @classmethod
    def from_provolatile(cls, provolatile: str) -> FunctionVolatility:
        """Convert a `pg_proc.provolatile` value to a `FunctionVolatility` enum."""
        if provolatile == "v":
            return cls.VOLATILE
        if provolatile == "s":
            return cls.STABLE
        if provolatile == "i":
            return cls.IMMUTABLE
        raise ValueError(f"Invalid volatility: {provolatile}")


def normalize_arg(arg: str) -> str:
    parts = arg.strip().split(maxsplit=1)
    if len(parts) == 2:
        name, type_str = parts
        norm_type = type_map.get(type_str.lower(), type_str.lower())
        # Handle array types
        if norm_type.endswith("[]"):
            base_type = norm_type[:-2]
            norm_base_type = type_map.get(base_type, base_type)
            norm_type = f"{norm_base_type}[]"

        return f"{name} {norm_type}"
    else:
        # Handle case where it might just be the type (e.g., from DROP FUNCTION)
        type_str = arg.strip()
        norm_type = type_map.get(type_str.lower(), type_str.lower())
        if norm_type.endswith("[]"):
            base_type = norm_type[:-2]
            norm_base_type = type_map.get(base_type, base_type)
            norm_type = f"{norm_base_type}[]"
        return norm_type


@dataclass
class Function(base.Function):
    """Describes a PostgreSQL function.

    Many attributes are not currently supported. Support is **currently**
    minimal due to being a means to an end for defining triggers, but can certainly
    be evaluated/added on request.
    """

    security: FunctionSecurity = FunctionSecurity.invoker

    #: Defines the parameters for the function, e.g. ["param1 int", "param2 varchar"]
    parameters: Optional[List[str]] = None

    #: Defines the volatility of the function.
    volatility: FunctionVolatility = FunctionVolatility.VOLATILE

    def to_sql_create(self, replace=False) -> list[str]:
        components = ["CREATE"]

        if replace:
            components.append("OR REPLACE")

        parameter_str = ""
        if self.parameters:
            parameter_str = ", ".join(self.parameters)

        components.append("FUNCTION")
        components.append(quote_name(self.qualified_name) + f"({parameter_str})")
        components.append(f"RETURNS {self.returns}")

        if self.security == FunctionSecurity.definer:
            components.append("SECURITY DEFINER")

        if self.volatility != FunctionVolatility.VOLATILE:
            components.append(self.volatility.value)

        components.append(f"LANGUAGE {self.language}")
        components.append(f"AS $${self.definition}$$")

        return [" ".join(components) + ";"]

    def to_sql_update(self) -> list[str]:
        return self.to_sql_create(replace=True)

    def to_sql_drop(self) -> list[str]:
        param_types = []
        if self.parameters:
            for param in self.parameters:
                # Naive split, assumes 'name type' or just 'type' format
                parts = param.split(maxsplit=1)
                if len(parts) == 2:
                    param_types.append(parts[1])
                else:
                    param_types.append(param) # Assume it's just the type if no space

        param_str = ", ".join(param_types)
        return [f"DROP FUNCTION {self.qualified_name}({param_str});"]

    def with_security(self, security: FunctionSecurity):
        return replace(self, security=security)

    def with_security_definer(self):
        return replace(self, security=FunctionSecurity.definer)

    def normalize(self) -> Function:
        definition = textwrap.dedent(self.definition)

        # Handle RETURNS TABLE(...) normalization
        returns_lower = self.returns.lower().strip()
        if returns_lower.startswith("table("):
            # Basic normalization: lowercase and remove extra spaces
            # This might need refinement for complex TABLE definitions
            inner_content = returns_lower[len("table("):-1].strip()
            cols = [normalize_arg(c) for c in inner_content.split(',')]
            normalized_returns = f"table({', '.join(cols)})"
        else:
            # Normalize base return type (including array types)
            norm_type = type_map.get(returns_lower, returns_lower)
            if norm_type.endswith("[]"):
                base = norm_type[:-2]
                norm_base = type_map.get(base, base)
                normalized_returns = f"{norm_base}[]"
            else:
                normalized_returns = norm_type

        # Normalize parameter types
        normalized_parameters = None
        if self.parameters:
            normalized_parameters = [normalize_arg(p) for p in self.parameters]

        return replace(
            self,
            definition=definition,
            returns=normalized_returns,
            parameters=normalized_parameters, # Use normalized parameters
        )


type_map = {
    "bigint": "int8",
    "bigserial": "serial8",
    "boolean": "bool",
    "character varying": "varchar",
    "character": "char",
    "double precision": "float8",
    "integer": "int4",
    "numeric": "decimal",
    "real": "float4",
    "smallint": "int2",
    "serial": "serial4",
    "time with time zone": "timetz",
    "timestamp with time zone": "timestamptz",
}
