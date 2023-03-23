from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from sqlalchemy import MetaData
from sqlalchemy.engine import Connection, Dialect

from sqlalchemy_declarative_extensions.dialects import get_views
from sqlalchemy_declarative_extensions.view.base import View, Views


@dataclass
class CreateViewOp:
    view: View

    def reverse(self):
        return DropViewOp(self.view)

    def to_sql(self, dialect: Dialect) -> list[str]:
        return self.view.to_sql_create(dialect)


@dataclass
class UpdateViewOp:
    from_view: View
    to_view: View

    def reverse(self):
        return UpdateViewOp(from_view=self.to_view, to_view=self.from_view)

    def to_sql(self, dialect: Dialect) -> list[str]:
        return self.to_view.to_sql_update(self.from_view, dialect)


@dataclass
class DropViewOp:
    view: View

    def reverse(self):
        return CreateViewOp(self.view)

    def to_sql(self, dialect: Dialect) -> list[str]:
        return self.view.to_sql_drop(dialect)


Operation = Union[CreateViewOp, UpdateViewOp, DropViewOp]


def compare_views(
    connection: Connection,
    views: Views,
    metadata: MetaData,
    normalize_with_connection: bool = True,
) -> list[Operation]:
    result: list[Operation] = []

    views_by_name = {r.qualified_name: r for r in views.views}
    expected_view_names = set(views_by_name)

    existing_views = get_views(connection)
    existing_views_by_name = {r.qualified_name: r for r in existing_views}
    existing_view_names = set(existing_views_by_name)

    new_view_names = expected_view_names - existing_view_names
    removed_view_names = existing_view_names - expected_view_names

    for view in views:
        view_name = view.qualified_name

        if view_name in views.ignore_views:
            continue

        view_created = view_name in new_view_names

        normalized_view = view.normalize(
            connection, metadata, using_connection=normalize_with_connection
        )

        if view_created:
            result.append(CreateViewOp(normalized_view))
        else:
            existing_view = existing_views_by_name[view_name]
            normalized_existing_view = existing_view.normalize(
                connection, metadata, using_connection=normalize_with_connection
            )

            if normalized_existing_view != normalized_view:
                result.append(UpdateViewOp(normalized_existing_view, normalized_view))

    if not views.ignore_unspecified:
        for removed_view in removed_view_names:
            if removed_view in views.ignore_views:
                continue

            view = existing_views_by_name[removed_view]
            result.append(DropViewOp(view))

    return result
