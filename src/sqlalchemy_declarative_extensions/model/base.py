from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Iterable, List, Optional, Union


@dataclass
class Models:
    models: List[Model] = field(default_factory=list)
    included_tables: List[str] = field(default_factory=list)
    ignore_unspecified: bool = False

    @classmethod
    def coerce_from_unknown(
        cls, unknown: Union[None, Iterable[Model], Models]
    ) -> Optional[Models]:
        if isinstance(unknown, Models):
            return unknown

        if isinstance(unknown, Iterable):
            return Models().are(*unknown)

        return None

    def __iter__(self):
        for role in self.models:
            yield role

    def are(self, *models: Model):
        return replace(self, models=models)

    def include_tables(self, *tables: str):
        return replace(self, included_tables=list(tables))


class Model:
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
