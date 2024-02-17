from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, TypeVar

from sqlalchemy import event
from sqlalchemy.sql.schema import MetaData

from sqlalchemy_declarative_extensions.function.base import Function, Functions
from sqlalchemy_declarative_extensions.grant.base import Grants
from sqlalchemy_declarative_extensions.role.base import Roles
from sqlalchemy_declarative_extensions.row.base import Row, Rows
from sqlalchemy_declarative_extensions.schema.base import Schemas
from sqlalchemy_declarative_extensions.sqlalchemy import HasMetaData
from sqlalchemy_declarative_extensions.trigger.base import Trigger, Triggers
from sqlalchemy_declarative_extensions.view.base import View, Views

if TYPE_CHECKING:
    from sqlalchemy_declarative_extensions.dialects import postgresql
    from sqlalchemy_declarative_extensions.grant.base import G
    from sqlalchemy_declarative_extensions.role import generic
    from sqlalchemy_declarative_extensions.schema.base import Schema


T = TypeVar("T")


def declarative_database(base: T) -> T:
    """Decorate a SQLAlchemy declarative base object to register database objects.

    See also :func:`sqlalchemy_declarative_extensions.declare_database`, of which this decorator is syntactic sugar.

    By decorating your declarative base with this decorator, the attributes
    "schemas", "roles", and "grants" are read and will register with SQLAlchemy
    and/or Alembic to ensure they're created during a ``metadata.create_createall``
    call or ``alembic --autogenerate``.

    Examples:
        >>> from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base
        >>> from sqlalchemy_declarative_extensions import declarative_database, Roles
        >>> from sqlalchemy_declarative_extensions.dialects.postgresql import Role
        >>>
        >>> _Base = declarative_base()

        >>> @declarative_database
        ... class Base(_Base):  # type: ignore
        ...     __abstract__ = True
        ...
        ...     schemas = Schemas().are('example')
        ...     roles = (
        ...         Roles(ignore_unspecified=True)
        ...         .are(
        ...             'read',
        ...             Role('fancy', createrole=True, in_roles=['read']),
        ...         )
        ...     )

    """
    raw_roles = getattr(base, "roles", None)
    raw_schemas = getattr(base, "schemas", None)
    raw_grants = getattr(base, "grants", None)
    raw_views = getattr(base, "views", None)
    raw_functions = getattr(base, "functions", None)
    raw_triggers = getattr(base, "triggers", None)
    raw_rows = getattr(base, "rows", None)

    metadata = getattr(base, "metadata", None)
    if metadata is None:  # pragma: no cover
        raise ValueError("Base must have a 'metadata' attribute.")

    declare_database(
        metadata,
        schemas=raw_schemas,
        roles=raw_roles,
        grants=raw_grants,
        views=raw_views,
        functions=raw_functions,
        triggers=raw_triggers,
        rows=raw_rows,
    )
    return base


def declare_database(
    metadata: MetaData,
    *,
    schemas: None | Iterable[Schema | str] | Schemas = None,
    roles: None | Iterable[generic.Role | postgresql.Role | str] | Roles = None,
    grants: None | Iterable[G] | Grants = None,
    views: None | Iterable[View] | Views = None,
    functions: None | Iterable[Function] | Functions = None,
    triggers: None | Iterable[Trigger] | Triggers = None,
    rows: None | Iterable[Row] | Rows = None,
):
    """Register declaratively specified database extension handlers.

    See also :func:`declarative_database` for alternative API which decorates
    a decalarative base class definition.

    This attaches the given declarative extensions onto the metadata such that
    they'll be recognized by SQLAlchemy's ``metadata.create_all`` call, as well
    as ``alembic --autogenerate`` (if you :func:`register_alembic_events`).

    .. note::

        The argument types are intentionally permissive. For simple schemas and
        roles especially, the most obvious and direct interface might literally
        be a list of strings, and as such that is an accepted input. Most documentation
        examples will reference the typed objects to which raw strings are coerced.

        For more complex examples, and especially if you need meta-options like
        ``ignore_unspecified``, you will need to use the objects directly.

    Arguments:
        metadata: The metadata on which the given extensions are being registered.
        schemas: The set of schemas to ensure exist.
        roles: The set of roles to ensure exist.
        grants: The set of grants to ensure are applied to the roles/schemas/tables.
        views: The set of views to ensure exist.
        functions: The set of functions to ensure exist.
        triggers: The set of triggers to ensure exist.
        rows: The set of rows to ensure are applied to the roles/schemas/tables.
    """
    metadata.info["schemas"] = Schemas.coerce_from_unknown(schemas)
    metadata.info["roles"] = Roles.coerce_from_unknown(roles)
    metadata.info["grants"] = Grants.coerce_from_unknown(grants)
    metadata.info["views"] = Views.coerce_from_unknown(views)
    metadata.info["functions"] = Functions.coerce_from_unknown(functions)
    metadata.info["triggers"] = Triggers.coerce_from_unknown(triggers)
    metadata.info["rows"] = Rows.coerce_from_unknown(rows)


def register_sqlalchemy_events(
    maybe_metadata: MetaData | HasMetaData,
    schemas=False,
    roles=False,
    grants=False,
    views=False,
    functions=False,
    triggers=False,
    rows=False,
):
    """Register handlers for supported object types into SQLAlchemy's event system.

    By default all object types are disabled, but each can be individually enabled.
    We assume most execution environments where one is using `MetaData.create_all`
    will be in tests; where roles and grants, in particular, are database-wide
    objects which can cause issues.

    Note this is the opposite of the defaults when registering against SQLAlchemy's
    event system.
    """
    from sqlalchemy_declarative_extensions.function.ddl import function_ddl
    from sqlalchemy_declarative_extensions.grant.ddl import grant_ddl
    from sqlalchemy_declarative_extensions.role.ddl import role_ddl
    from sqlalchemy_declarative_extensions.row.query import rows_query
    from sqlalchemy_declarative_extensions.schema.ddl import schema_ddl
    from sqlalchemy_declarative_extensions.trigger.ddl import trigger_ddl
    from sqlalchemy_declarative_extensions.view.ddl import view_ddl

    if isinstance(maybe_metadata, MetaData):
        metadata = maybe_metadata
    else:
        metadata = maybe_metadata.metadata

    concrete_schemas = metadata.info.get("schemas")
    concrete_roles = metadata.info.get("roles")
    concrete_grants = metadata.info.get("grants")
    concrete_views = metadata.info.get("views")
    concrete_functions = metadata.info.get("functions")
    concrete_triggers = metadata.info.get("triggers")
    concrete_rows = metadata.info.get("rows")

    if concrete_schemas and schemas:
        event.listen(
            metadata,
            "before_create",
            schema_ddl,
        )

    if concrete_roles and roles:
        event.listen(
            metadata,
            "before_create",
            role_ddl,
        )

    if concrete_grants and grants:
        event.listen(
            metadata,
            "before_create",
            grant_ddl(concrete_grants, after=False),
        )

        event.listen(
            metadata,
            "after_create",
            grant_ddl(concrete_grants, after=True),
        )

    if concrete_views and views:
        event.listen(
            metadata,
            "after_create",
            view_ddl(concrete_views),
        )

    if concrete_functions and functions:
        event.listen(
            metadata,
            "after_create",
            function_ddl(concrete_functions),
        )

    if concrete_triggers and triggers:
        event.listen(
            metadata,
            "after_create",
            trigger_ddl(concrete_triggers),
        )

    if concrete_rows and rows:
        event.listen(
            metadata,
            "after_create",
            rows_query(concrete_rows),
        )
