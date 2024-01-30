from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Iterable


@dataclass
class Rows:
    rows: list[Row] = field(default_factory=list)
    included_tables: list[str] = field(default_factory=list)
    ignore_unspecified: bool = False

    @classmethod
    def coerce_from_unknown(cls, unknown: None | Iterable[Row] | Rows) -> Rows | None:
        if isinstance(unknown, Rows):
            return unknown

        if isinstance(unknown, Iterable):
            return Rows().are(*unknown)

        return None

    def __iter__(self):
        yield from self.rows

    def are(self, *rows: Row):
        return replace(self, rows=rows)


@dataclass
class Row:
    schema: str | None
    tablename: str
    column_values: dict[str, Any]

    def __init__(self, tablename, **column_values):
        try:
            schema, table = tablename.split(".", 1)
        except ValueError:
            self.schema = None
            self.tablename = tablename
        else:
            self.schema = schema
            self.tablename = table

        self.column_values = column_values

    @property
    def qualified_name(self):
        if self.schema:
            return f"{self.schema}.{self.tablename}"
        return self.tablename


@dataclass
class Table:
    """Convenience class for producing multiple rows against the same table.

    Examples:
        Rows might be created directly, like so:

        >>> [
        ...     Row("users", id=1, name="John", active=True),
        ...     Row("users", id=2, name="Bob", active=True),
        ... ]
        [Row(schema=None, tablename='users', column_values={'id': 1, 'name': 'John', 'active': True}), Row(schema=None, tablename='users', column_values={'id': 2, 'name': 'Bob', 'active': True})]

        But use of `Table` can help elide repetition among those rows:

        >>> users = Table("users", active=True)
        >>> [
        ...     users.row(id=1, name="John"),
        ...     users.row(id=2, name="Bob"),
        ... ]
        [Row(schema=None, tablename='users', column_values={'active': True, 'id': 1, 'name': 'John'}), Row(schema=None, tablename='users', column_values={'active': True, 'id': 2, 'name': 'Bob'})]
    """
    name: str
    column_values: dict[str, Any]

    def __init__(self, name, **column_values):
        self.name = name
        self.column_values = column_values

    def row(self, **column_values) -> Row:
        final_values= {**self.column_values, **column_values}
        return Row(self.name, **final_values)
