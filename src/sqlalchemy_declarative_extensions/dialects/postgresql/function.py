from __future__ import annotations

import textwrap
from dataclasses import dataclass, replace

from sqlalchemy_declarative_extensions.function import base


@dataclass
class Function(base.Function):
    """Describes a PostgreSQL function.

    Many function attributes are not currently supported. Support is **currently**
    minimal due to being a means to an end for defining triggers.
    """

    @classmethod
    def from_unknown_function(cls, f: base.Function | Function) -> Function:
        if not isinstance(f, Function):
            return Function(
                name=f.name,
                definition=f.definition,
                returns=f.returns,
                language=f.language,
                schema=f.schema,
            )

        return f

    def normalize(self) -> Function:
        returns = self.returns.lower()
        definition = textwrap.dedent(self.definition)
        return replace(
            self, returns=type_map.get(returns, returns), definition=definition
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
