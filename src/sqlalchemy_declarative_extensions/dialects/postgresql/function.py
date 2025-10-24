from __future__ import annotations

import enum
import re
import textwrap
from dataclasses import dataclass, replace
from typing import Any, List, Literal, Sequence, Tuple, cast

from sqlalchemy import Column

from sqlalchemy_declarative_extensions.function import base
from sqlalchemy_declarative_extensions.sql import quote_name

_sqlbody_regex = re.compile(r"\W*(BEGIN ATOMIC|RETURN)\W", re.IGNORECASE | re.MULTILINE)
"""sql_body
The body of a LANGUAGE SQL function. This can either be a single statement

RETURN expression

or a block

BEGIN ATOMIC
  statement;
  statement;
  ...
  statement;
END
"""


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


@dataclass
class Function(base.Function):
    """Describes a PostgreSQL function.

    Not all functionality is currently implemented, but can be evaluated/added on request.
    """

    security: FunctionSecurity = FunctionSecurity.invoker
    returns: FunctionReturn | str | None = None  # type: ignore
    parameters: Sequence[FunctionParam | str] | None = None  # type: ignore
    volatility: FunctionVolatility = FunctionVolatility.VOLATILE

    @property
    def _has_sqlbody(self) -> bool:
        return self.language.lower() == "sql" and bool(
            _sqlbody_regex.match(self.definition)
        )

    def to_sql_create(self, replace=False) -> list[str]:
        components = ["CREATE"]

        if replace:
            components.append("OR REPLACE")

        parameter_str = ""
        if self.parameters:
            parameter_str = ", ".join(
                cast(FunctionParam, p).to_sql_create() for p in self.parameters
            )

        components.append("FUNCTION")
        components.append(quote_name(self.qualified_name) + f"({parameter_str})")

        returns = cast(FunctionReturn, self.returns)
        components.append(f"RETURNS {returns.to_sql_create()}")

        if self.security == FunctionSecurity.definer:
            components.append("SECURITY DEFINER")

        if self.volatility != FunctionVolatility.VOLATILE:
            components.append(self.volatility.value)

        components.append(f"LANGUAGE {self.language}")
        if self._has_sqlbody:
            components.append(self.definition)
        else:
            components.append(f"AS $${self.definition}$$")

        return [" ".join(components) + ";"]

    def to_sql_update(self) -> list[str]:
        return self.to_sql_create(replace=True)

    def to_sql_drop(self) -> list[str]:
        param_str = ""
        if self.parameters:
            param_str = ", ".join(
                cast(FunctionParam, p).to_sql_drop() for p in self.parameters
            )

        return [f"DROP FUNCTION {self.qualified_name}({param_str});"]

    def with_security(self, security: FunctionSecurity):
        return replace(self, security=security)

    def with_security_definer(self):
        return replace(self, security=FunctionSecurity.definer)

    def normalize(self) -> Function:
        definition = textwrap.dedent(self.definition)
        if self._has_sqlbody:
            definition = definition.strip()

        # Normalize parameter types
        parameters = []
        if self.parameters:
            parameters = [
                FunctionParam.from_unknown(p).normalize() for p in self.parameters
            ]

        input_parameters = [p for p in parameters if p.is_input]
        table_parameters = [p for p in parameters if p.is_table]

        returns = FunctionReturn.from_unknown(self.returns, parameters=table_parameters)
        if returns:
            returns = returns.normalize()

        return replace(
            self,
            definition=definition,
            returns=returns,
            parameters=input_parameters,
        )


@dataclass
class FunctionParam:
    name: str | None
    type: str
    default: Any | None = None
    mode: Literal["i", "o", "b", "v", "t"] | None = None

    @classmethod
    def input(cls, name: str, type: str, default: Any | None = None) -> FunctionParam:
        """Create an input parameter."""
        return cls(name=name, type=type, default=default, mode="i")

    @classmethod
    def output(cls, name: str, type: str, default: Any | None = None) -> FunctionParam:
        """Create an input parameter."""
        return cls(name=name, type=type, default=default, mode="o")

    @classmethod
    def inout(cls, name: str, type: str, default: Any | None = None) -> FunctionParam:
        """Create an input parameter."""
        return cls(name=name, type=type, default=default, mode="b")

    @classmethod
    def variadic(
        cls, name: str, type: str, default: Any | None = None
    ) -> FunctionParam:
        """Create an input parameter."""
        return cls(name=name, type=type, default=default, mode="v")

    @classmethod
    def table(cls, name: str, type: str, default: Any | None = None) -> FunctionParam:
        """Create an input parameter."""
        return cls(name=name, type=type, default=default, mode="t")

    @classmethod
    def from_unknown(
        cls, source_param: str | tuple[str, str] | FunctionParam
    ) -> FunctionParam:
        if isinstance(source_param, FunctionParam):
            return source_param

        if isinstance(source_param, tuple):
            return cls(*source_param)

        try:
            name, type = source_param.strip().split(maxsplit=1)
        except ValueError:
            name = None
            type = source_param.strip()

        return cls(name, type)

    def normalize(self) -> FunctionParam:
        type = self.type.lower()
        return replace(
            self,
            name=self.name.lower() if self.name is not None else None,
            mode=self.mode or "i",
            type=type_map.get(type, type),
            default=str(self.default) if self.default is not None else None,
        )

    def to_sql_create(self) -> str:
        segments = []
        if self.mode:
            modes = {"o": "OUT ", "b": "INOUT ", "v": "VARIADIC ", "t": "TABLE "}
            mode = modes.get(self.mode)
            if mode:
                segments.append(mode)

        if self.name:
            segments.append(self.name)

        segments.append(self.type)

        if self.default is not None:
            segments.append(f"DEFAULT {self.default}")
        return " ".join(segments)

    def to_sql_drop(self) -> str:
        return self.type

    @property
    def is_input(self) -> bool:
        """Check if the parameter is an input parameter."""
        return self.mode not in {"o", "t"}

    @property
    def is_table(self) -> bool:
        return self.mode == "t"


@dataclass
class FunctionReturn:
    value: str | None = None
    table: Sequence[Column | tuple[str, str] | str] | None = None

    @classmethod
    def from_unknown(
        cls,
        source: str | FunctionReturn | None,
        parameters: list[FunctionParam] | None = None,
    ) -> FunctionReturn | None:
        if source is None:
            return None

        if isinstance(source, FunctionReturn):
            return source

        # Handle RETURNS TABLE(...) normalization
        returns_lower = source.lower().strip()
        if returns_lower.startswith("table("):
            table_return_params = [
                (p.name, p.type) for p in (parameters or []) if p.name and p.mode == "t"
            ]

            if not table_return_params:
                raise NotImplementedError(
                    "TABLE return types must either be provided as a `FunctionReturn(table=...)` construct "
                    "or as input parameters of type `FunctionParam.table(...)."
                )

            return cls(table=table_return_params)

        # Normalize base return type (including array types)
        norm_type = type_map.get(returns_lower, returns_lower)
        if norm_type.endswith("[]"):
            base = norm_type[:-2]
            norm_base = type_map.get(base, base)
            normalized_returns = f"{norm_base}[]"
        else:
            normalized_returns = norm_type

        return cls(value=normalized_returns)

    def normalize(self) -> FunctionReturn:
        value = self.value

        table = self.table
        if self.table:
            table = []
            for arg in self.table:
                if isinstance(arg, Column):
                    arg_name = arg.name
                    arg_type = arg.type.compile()
                elif isinstance(arg, tuple):
                    arg_name, arg_type = arg
                else:
                    arg_name, arg_type = arg.strip().split(maxsplit=1)

                arg_type = arg_type.lower()
                arg_type = type_map.get(arg_type, arg_type)
                table.append((arg_name.lower(), arg_type))

        return replace(self, value=value, table=table)

    def to_sql_create(self) -> str:
        if self.value:
            return self.value

        if self.table:
            table = cast(List[Tuple[str, str]], self.table)
            table_args = ", ".join(f"{name} {type}" for name, type in table)
            return f"TABLE({table_args})"

        return "void"


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
    "char[]": "_char",
    "varchar[]": "_varchar",
    "text[]": "_text",
    "int4[]": "_int4",
    "integer[]": "_int4",
    "bool[]": "_bool",
    "boolean[]": "_bool",
}
