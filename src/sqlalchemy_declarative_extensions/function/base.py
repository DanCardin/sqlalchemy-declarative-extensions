from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Iterable

from sqlalchemy_declarative_extensions.sql import qualify_name
from sqlalchemy_declarative_extensions.sqlalchemy import HasMetaData, MetaData


@dataclass
class Function:
    """Describes a user defined function.

    Many function attributes are not currently supported. Support is **currently**
    minimal due to being a means to an end for defining triggers.
    """

    name: str
    definition: str
    returns: str = "void"
    language: str = "sql"
    schema: str | None = None

    @property
    def qualified_name(self):
        return qualify_name(self.schema, self.name)

    def normalize(self) -> Function:
        raise NotImplementedError()  # pragma: no cover

    def to_sql_create(self, replace=False):
        components = ["CREATE"]

        if replace:
            components.append("OR REPLACE")

        components.append("FUNCTION")
        components.append(self.qualified_name + "()")

        if self.returns:
            components.append(f"RETURNS {self.returns}")

        components.append(f"LANGUAGE {self.language}")
        components.append(f"AS $${self.definition}$$")

        return " ".join(components) + ";"

    def to_sql_update(self):
        return self.to_sql_create(replace=True)

    def to_sql_drop(self):
        return f"DROP FUNCTION {self.qualified_name}();"


@dataclass
class Functions:
    functions: list[Function] = field(default_factory=list)

    ignore_unspecified: bool = False

    @classmethod
    def coerce_from_unknown(
        cls, unknown: None | Iterable[Function] | Functions
    ) -> Functions | None:
        if isinstance(unknown, Functions):
            return unknown

        if isinstance(unknown, Iterable):
            return cls().are(*unknown)

        return None

    def append(self, function: Function):
        self.functions.append(function)

    def __iter__(self):
        yield from self.functions

    def are(self, *functions: Function):
        return replace(self, functions=functions)


def register_function(base_or_metadata: HasMetaData | MetaData, function: Function):
    """Register a function onto the given declarative base or `Metadata`.

    This can be used instead of the static registration through `Functions` on a declarative base or
    `MetaData`, to imperitively register functions.
    """
    if isinstance(base_or_metadata, MetaData):
        metadata = base_or_metadata
    else:
        metadata = base_or_metadata.metadata

    if not metadata.info.get("functions"):
        metadata.info["functions"] = Functions()
    metadata.info["functions"].append(function)
