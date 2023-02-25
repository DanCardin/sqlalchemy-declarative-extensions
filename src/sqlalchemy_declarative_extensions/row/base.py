from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Iterable


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


class Row:
    def __init__(self, tablename, **column_values):
        try:
            schema, table = tablename.split(".", 1)
        except ValueError:
            self.schema = None
            self.tablename = tablename
        else:
            self.schema = schema
            self.tablename = table

        self.qualified_name = tablename
        self.column_values = column_values
