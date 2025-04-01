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
        returns = self.returns.lower()
        return replace(
            self, definition=definition, returns=type_map.get(returns, returns)
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
