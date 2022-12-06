from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from sqlalchemy.engine import Connection, Dialect

from sqlalchemy_declarative_extensions.dialects import get_views
from sqlalchemy_declarative_extensions.view.base import View, Views


@dataclass
class CreateViewOp:
    view: View

    @classmethod
    def create_view(
        cls,
        operations,
        view_name: str,
        definition: str,
        *,
        schema: str | None = None,
        materialized: bool = False,
    ):
        op = cls(View(view_name, definition, schema=schema, materialized=materialized))
        return operations.invoke(op)

    def reverse(self):
        return DropViewOp(self.view)

    def to_sql(self, dialect: Dialect):
        return self.view.to_sql_create(dialect)


@dataclass
class DropViewOp:
    view: View

    @classmethod
    def drop_view(cls, operations, view_name: str, schema: str | None = None):
        op = cls(View(view_name, definition="", schema=schema))
        return operations.invoke(op)

    def reverse(self):
        return CreateViewOp(self.view)

    def to_sql(self, _=None):
        return self.view.to_sql_drop()


Operation = Union[CreateViewOp, DropViewOp]


def compare_views(connection: Connection, views: Views) -> list[Operation]:
    result: list[Operation] = []
    if not views:
        return result

    views_by_name = {r.qualified_name: r for r in views.views}
    expected_view_names = set(views_by_name)

    existing_views = get_views(connection)
    existing_views_by_name = {r.qualified_name: r for r in existing_views}
    existing_view_names = set(existing_views_by_name)

    new_view_names = expected_view_names - existing_view_names
    removed_view_names = existing_view_names - expected_view_names

    for view in views.views:
        view_name = view.qualified_name

        if view_name in views.ignore_views:
            continue

        view_created = view_name in new_view_names

        if view_created:
            result.append(CreateViewOp(view))
        else:
            existing_view = existing_views_by_name[view_name]

            view_updated = not existing_view.equals(view, connection.dialect)
            if view_updated:
                existing_view = existing_views_by_name[view_name]
                result.append(DropViewOp(view))
                result.append(CreateViewOp(view))

    if not views.ignore_unspecified:
        for removed_view in removed_view_names:
            if removed_view in views.ignore_views:
                continue

            view = existing_views_by_name[removed_view]
            result.append(DropViewOp(view))

    return result
