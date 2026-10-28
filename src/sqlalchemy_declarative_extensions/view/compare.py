from __future__ import annotations

import warnings
from dataclasses import dataclass, replace
from glob import escape
from typing import Union

from sqlalchemy.engine import Connection, Dialect

from sqlalchemy_declarative_extensions.dialects import get_view_cls, get_views
from sqlalchemy_declarative_extensions.op import ExecuteOp
from sqlalchemy_declarative_extensions.sql import is_ignored
from sqlalchemy_declarative_extensions.view.base import View, Views


@dataclass
class CreateViewOp(ExecuteOp):
    view: View

    def reverse(self):
        return DropViewOp(self.view)

    def to_sql(self, dialect: Dialect | None = None) -> list[str]:
        return self.view.to_sql_create(dialect)


@dataclass
class UpdateViewOp(ExecuteOp):
    from_view: View
    view: View

    def reverse(self):
        return UpdateViewOp(from_view=self.view, view=self.from_view)

    def to_sql(self, dialect: Dialect | None = None) -> list[str]:
        return self.view.to_sql_update(self.from_view, dialect)


@dataclass
class DropViewOp(ExecuteOp):
    view: View

    def reverse(self):
        return CreateViewOp(self.view)

    def to_sql(self, dialect: Dialect | None = None) -> list[str]:
        return self.view.to_sql_drop(dialect)


Operation = Union[CreateViewOp, UpdateViewOp, DropViewOp]


def compare_views(
    connection: Connection,
    views: Views,
    normalize_with_connection: bool = True,
) -> list[Operation]:
    if views.ignore_views:
        warnings.warn(
            "`ignore_views` is deprecated, use `ignore` instead", DeprecationWarning
        )
        views = replace(views, ignore=list(views.ignore_views) + list(views.ignore))

    result: list[Operation] = []

    view_cls = get_view_cls(connection)
    concrete_defined_views: list[View] = [
        view_cls.coerce_from_unknown(view) for view in views.views
    ]

    views_by_name = {r.qualified_name: r for r in concrete_defined_views}
    expected_view_names = set(views_by_name)

    # Declared views are always compared. Otherwise a declared view outside of `include` would
    # not be found, and so would be created again (and fail) on every run.
    include = views.include
    if include is not None:
        include = [*include, *(escape(name) for name in expected_view_names)]

    existing_views = get_views(connection, ignore=views.ignore, include=include)
    existing_views_by_name = {r.qualified_name: r for r in existing_views}
    existing_view_names = set(existing_views_by_name)

    new_view_names = expected_view_names - existing_view_names
    removed_view_names = existing_view_names - expected_view_names

    for view in concrete_defined_views:
        normalized_view = view.normalize(
            connection, views.naming_convention, using_connection=False
        )

        view_name = normalized_view.qualified_name

        if is_ignored(view_name, views.ignore):
            continue

        view_created = view_name in new_view_names

        if view_created:
            result.append(CreateViewOp(normalized_view))
        else:
            normalized_view = normalized_view.normalize(
                connection,
                views.naming_convention,
                using_connection=normalize_with_connection,
            )

            existing_view = existing_views_by_name[view_name]
            normalized_existing_view = existing_view.normalize(
                connection,
                views.naming_convention,
                using_connection=normalize_with_connection,
            )

            if normalized_existing_view != normalized_view:
                result.append(UpdateViewOp(normalized_existing_view, normalized_view))

    if not views.ignore_unspecified:
        for removed_view in removed_view_names:
            if is_ignored(removed_view, views.ignore):
                continue

            view = existing_views_by_name[removed_view]
            result.append(DropViewOp(view))

    return result
