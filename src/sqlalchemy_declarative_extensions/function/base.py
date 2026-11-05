from __future__ import annotations

import glob
from dataclasses import dataclass, field, replace
from typing import Iterable, Sequence

from sqlalchemy import MetaData
from typing_extensions import Self

from sqlalchemy_declarative_extensions.sql import qualify_name, quote_name
from sqlalchemy_declarative_extensions.sqlalchemy import HasMetaData


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

    #: Defines the parameters for the function, e.g. ["param1 int", "param2 varchar"]
    parameters: Sequence[str] | None = None
    """List of parameter definitions as strings, e.g., `['param1 int', 'param2 varchar']`.
    The comparison logic parses these strings to compare parameter names and types.
    """

    @classmethod
    def from_unknown_function(cls, f: Function) -> Self:
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

    @property
    def qualified_name(self):
        return qualify_name(self.schema, self.name)

    def normalize(self) -> Self:
        raise NotImplementedError()  # pragma: no cover

    def to_sql_create(self) -> list[str]:
        raise NotImplementedError()

    def to_sql_update(self) -> list[str]:
        return [
            *self.to_sql_drop(),
            *self.to_sql_create(),
        ]

    def to_sql_drop(self) -> list[str]:
        # Base implementation can only reliably drop functions without parameters
        # since function overloads are determined by parameter types in most SQL dialects.
        # Dialect-specific implementations should handle cases with parameters.
        if self.parameters:
            raise NotImplementedError(
                "Dropping functions with parameters must be implemented by dialect-specific subclasses"
            )
        return [f"DROP FUNCTION {quote_name(self.qualified_name)}();"]

    def with_name(self, name: str):
        return replace(self, name=name)

    def with_language(self, language: str):
        return replace(self, language=language)

    def with_return_type(self, return_type: str):
        return replace(self, returns=return_type)


@dataclass
class Functions:
    """The collection of functions and associated options comparisons.

    Note: `ignore` option accepts a sequence of strings. Each string is individually
        interpreted as a "glob". This means a string like "foo.*" would ignore all views
        contained within the schema "foo".
    """

    functions: list[Function] = field(default_factory=list)

    include: list[str] | None = None
    ignore: list[str] = field(default_factory=list)
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

    @classmethod
    def extract(cls, metadata: MetaData | list[MetaData | None] | None) -> Self | None:
        """Extract the declared functions, including those executed by declared triggers.

        When a trigger function is not otherwise declared, only that function is managed
        (through `include`), so unrelated functions in the database are left alone.
        """
        if not isinstance(metadata, Sequence):
            metadata = [metadata]

        declared = cls._extract_declared(metadata)
        trigger_functions = [
            function
            for m in metadata
            if m and m.info.get("triggers")
            for function in m.info["triggers"].functions
        ]
        if not trigger_functions:
            return declared

        if declared is None:
            result = cls(include=[])
        else:
            result = replace(declared, functions=list(declared.functions))

        for function in trigger_functions:
            result.append_managed(function)
        return result

    @classmethod
    def _extract_declared(cls, metadata: Sequence[MetaData | None]) -> Self | None:
        instances: list[Self] = [
            m.info["functions"] for m in metadata if m and m.info.get("functions")
        ]

        instance_count = len(instances)
        if instance_count == 0:
            return None

        if instance_count == 1:
            return instances[0]

        if not all(
            x.ignore_unspecified == instances[0].ignore_unspecified for x in instances
        ):
            raise ValueError(
                "All combined `Functions` instances must agree on the set of settings: ignore_unspecified"
            )

        functions = [s for instance in instances for s in instance.functions]
        # Preserve None if all instances have include=None, otherwise combine all non-None includes
        include_values = [
            instance.include for instance in instances if instance.include is not None
        ]
        include = [s for inc in include_values for s in inc] if include_values else None
        ignore = [s for instance in instances for s in instance.ignore]
        ignore_unspecified = instances[0].ignore_unspecified
        return cls(
            functions=functions,
            ignore_unspecified=ignore_unspecified,
            ignore=ignore,
            include=include,
        )

    def append(self, function: Function):
        """Add the function, unless an identical one is already present.

        Raises a `ValueError` if a different function has the same qualified name.
        """
        qualified_name = function.qualified_name
        existing = next(
            (f for f in self.functions if f.qualified_name == qualified_name), None
        )
        if existing is not None:
            if existing != function:
                raise ValueError(
                    f"Function '{qualified_name}' is declared more than once"
                    " with differing definitions."
                )
            return

        self.functions.append(function)

    def append_managed(self, function: Function):
        """Append the function, and add it to `include` if this collection is restricted by it."""
        self.append(function)

        if self.include is None:
            return

        pattern = glob.escape(function.qualified_name)
        if pattern not in self.include:
            self.include = [*self.include, pattern]

    def __iter__(self):
        yield from self.functions

    def are(self, *functions: Function):
        return replace(self, functions=list(functions))


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
