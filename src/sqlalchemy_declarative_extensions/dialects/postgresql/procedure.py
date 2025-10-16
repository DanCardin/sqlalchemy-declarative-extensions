from __future__ import annotations

import enum
import re
import textwrap
from dataclasses import dataclass, replace

from typing_extensions import Self

from sqlalchemy_declarative_extensions.procedure import base
from sqlalchemy_declarative_extensions.sql import quote_name

_sqlbody_regex = re.compile(r"\W?(BEGIN ATOMIC)\W", re.IGNORECASE | re.MULTILINE)
"""sql_body
The body of a LANGUAGE SQL procedure. This should be a block

BEGIN ATOMIC
  statement;
  statement;
  ...
  statement;
END
"""


@enum.unique
class ProcedureSecurity(enum.Enum):
    invoker = "INVOKER"
    definer = "DEFINER"


@dataclass
class Procedure(base.Procedure):
    """Describes a PostgreSQL procedure.

    Many attributes are not currently supported. Support is **currently**
    minimal due to being a means to an end for defining triggers, but can certainly
    be evaluated/added on request.
    """

    security: ProcedureSecurity = ProcedureSecurity.invoker

    @property
    def _has_sqlbody(self) -> bool:
        return self.language.lower() == "sql" and _sqlbody_regex.match(self.definition)

    def to_sql_create(self, replace=False) -> list[str]:
        components = ["CREATE"]

        if replace:
            components.append("OR REPLACE")

        components.append("PROCEDURE")
        components.append(quote_name(self.qualified_name) + "()")

        if self.security == ProcedureSecurity.definer:
            components.append("SECURITY DEFINER")

        components.append(f"LANGUAGE {self.language}")
        if self._has_sqlbody:
            components.append(self.definition)
        else:
            components.append(f"AS $${self.definition}$$")

        return [" ".join(components) + ";"]

    def to_sql_update(self) -> list[str]:
        return self.to_sql_create(replace=True)

    def normalize(self) -> Self:
        definition = textwrap.dedent(self.definition)
        if self._has_sqlbody:
            definition = definition.strip()
        return replace(self, definition=definition)

    def with_security(self, security: ProcedureSecurity):
        return replace(self, security=security)

    def with_security_definer(self):
        return replace(self, security=ProcedureSecurity.definer)


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
