from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, TypeVar

from sqlalchemy import event
from sqlalchemy.sql.schema import MetaData

from sqlalchemy_declarative_extensions.database.base import Databases
from sqlalchemy_declarative_extensions.function.base import Function, Functions
from sqlalchemy_declarative_extensions.grant.base import Grants
from sqlalchemy_declarative_extensions.procedure.base import Procedure, Procedures
from sqlalchemy_declarative_extensions.role.base import Roles
from sqlalchemy_declarative_extensions.row.base import Row, Rows
from sqlalchemy_declarative_extensions.schema.base import Schemas
from sqlalchemy_declarative_extensions.sqlalchemy import HasMetaData
from sqlalchemy_declarative_extensions.trigger.base import Trigger, Triggers
from sqlalchemy_declarative_extensions.view.base import View, Views

if TYPE_CHECKING:
    from sqlalchemy_declarative_extensions.database.base import Database
    from sqlalchemy_declarative_extensions.dialects import postgresql
    from sqlalchemy_declarative_extensions.grant.base import G
    from sqlalchemy_declarative_extensions.role import generic
    from sqlalchemy_declarative_extensions.schema.base import Schema


T = TypeVar("T")


def declarative_database(base: T) -> T:
    """Decorate a SQLAlchemy declarative base object to register database objects.

    See also :func:`sqlalchemy_declarative_extensions.declare_database`, of which this decorator is syntactic sugar.

    By decorating your declarative base with this decorator, the attributes
    "schemas", "roles", "grants", etc are read and will register with SQLAlchemy
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
    raw_procedures = getattr(base, "procedures", None)
    raw_functions = getattr(base, "functions", None)
    raw_triggers = getattr(base, "triggers", None)
    raw_databases = getattr(base, "databases", None)
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
        procedures=raw_procedures,
        functions=raw_functions,
        triggers=raw_triggers,
        databases=raw_databases,
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
    procedures: None | Iterable[Procedure] | Procedures = None,
    functions: None | Iterable[Function] | Functions = None,
    triggers: None | Iterable[Trigger] | Triggers = None,
    databases: None | Iterable[Database] | Databases = None,
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
        procedures: The set of procedures to ensure exist.
        functions: The set of functions to ensure exist.
        triggers: The set of triggers to ensure exist.
        databases: The set of databases to ensure exist.
        rows: The set of rows to ensure are applied to the roles/schemas/tables.
    """
    metadata.info["schemas"] = Schemas.coerce_from_unknown(schemas)
    metadata.info["roles"] = Roles.coerce_from_unknown(roles)
    metadata.info["grants"] = Grants.coerce_from_unknown(grants)
    metadata.info["views"] = Views.coerce_from_unknown(views)
    metadata.info["procedures"] = Procedures.coerce_from_unknown(procedures)
    metadata.info["functions"] = Functions.coerce_from_unknown(functions)
    metadata.info["triggers"] = Triggers.coerce_from_unknown(triggers)
    metadata.info["databases"] = Databases.coerce_from_unknown(databases)
    metadata.info["rows"] = Rows.coerce_from_unknown(rows)


def register_sqlalchemy_events(
    maybe_metadata: MetaData | HasMetaData,
    *,
    databases: bool | list[str] = False,
    schemas: bool | list[str] = False,
    roles: bool | list[str] = False,
    grants: bool = False,
    views: bool | list[str] = False,
    procedures: bool | list[str] = False,
    functions: bool | list[str] = False,
    triggers: bool | list[str] = False,
    rows: bool | list[str] = False,
):
    """Register handlers for supported object types into SQLAlchemy's event system.

    By default all object types are disabled, but each can be individually enabled.
    We assume most execution environments where one is using `MetaData.create_all`
    will be in tests; where roles and grants, in particular, are database-wide
    objects which can cause issues.

    Note this is the opposite of the defaults when registering against SQLAlchemy's
    event system.

    Valid parameter/flag values include:

        - bool: Enables all objects of that object type
        - list[str]: Performs a glob-match of each item by its unique identifier (typically name),
                     and ignores all non-matching objects.
    """
    if isinstance(maybe_metadata, MetaData):
        metadata = maybe_metadata
    else:
        metadata = maybe_metadata.metadata

    register_create_events(
        metadata,
        databases=databases,
        schemas=schemas,
        roles=roles,
        grants=grants,
        views=views,
        procedures=procedures,
        functions=functions,
        triggers=triggers,
        rows=rows,
    )

    register_drop_events(
        metadata,
        databases=databases,
        schemas=schemas,
        roles=roles,
        views=views,
        procedures=procedures,
        functions=functions,
        triggers=triggers,
    )


def register_create_events(
    metadata: MetaData,
    *,
    databases: bool | list[str] = False,
    schemas: bool | list[str] = False,
    roles: bool | list[str] = False,
    grants: bool = False,
    views: bool | list[str] = False,
    procedures: bool | list[str] = False,
    functions: bool | list[str] = False,
    triggers: bool | list[str] = False,
    rows: bool | list[str] = False,
):
    from sqlalchemy_declarative_extensions.database.ddl import database_ddl
    from sqlalchemy_declarative_extensions.function.ddl import function_ddl
    from sqlalchemy_declarative_extensions.grant.ddl import grant_ddl
    from sqlalchemy_declarative_extensions.procedure.ddl import procedure_ddl
    from sqlalchemy_declarative_extensions.role.ddl import role_ddl
    from sqlalchemy_declarative_extensions.row.query import rows_query
    from sqlalchemy_declarative_extensions.schema.ddl import schema_ddl
    from sqlalchemy_declarative_extensions.trigger.ddl import trigger_ddl
    from sqlalchemy_declarative_extensions.view.ddl import view_ddl

    concrete_schemas = metadata.info.get("schemas") or Schemas()
    concrete_roles = metadata.info.get("roles") or Roles()
    concrete_grants = metadata.info.get("grants") or Grants()
    concrete_views = Views.extract(metadata) or Views()
    concrete_procedures = metadata.info.get("procedures") or Procedures()
    concrete_functions = metadata.info.get("functions") or Functions()
    concrete_triggers = metadata.info.get("triggers") or Triggers()
    concrete_databases = metadata.info.get("databases") or Databases()
    concrete_rows = metadata.info.get("rows") or Rows()

    if databases:
        database_filter = databases if isinstance(databases, list) else None
        event.listen(
            metadata,
            "before_create",
            database_ddl(concrete_databases, database_filter),
        )

    if schemas:
        schema_filter = schemas if isinstance(schemas, list) else None
        event.listen(
            metadata,
            "before_create",
            schema_ddl(concrete_schemas, schema_filter),
        )

    if roles:
        role_filter = roles if isinstance(roles, list) else None
        event.listen(
            metadata,
            "before_create",
            role_ddl(concrete_roles, role_filter),
        )

    if grants:
        event.listen(
            metadata,
            "before_create",
            grant_ddl(concrete_grants, concrete_roles),
        )
        # There should(?) be no need to handle dropping for grants,
        # they will be handled directly by table handling.

    if views:
        view_filter = views if isinstance(views, list) else None
        event.listen(
            metadata,
            "after_create",
            view_ddl(concrete_views, view_filter),
        )

    if procedures:
        procedure_filter = procedures if isinstance(procedures, list) else None
        event.listen(
            metadata,
            "after_create",
            procedure_ddl(concrete_procedures, procedure_filter),
        )

    if functions:
        function_filter = functions if isinstance(functions, list) else None
        event.listen(
            metadata,
            "after_create",
            function_ddl(concrete_functions, function_filter),
        )

    if triggers:
        trigger_filter = triggers if isinstance(triggers, list) else None
        event.listen(
            metadata,
            "after_create",
            trigger_ddl(concrete_triggers, trigger_filter),
        )

    if rows:
        row_filter = rows if isinstance(rows, list) else None
        event.listen(
            metadata,
            "after_create",
            rows_query(concrete_rows, row_filter),
        )


def register_drop_events(
    metadata: MetaData,
    *,
    databases: bool | list[str] = False,
    schemas: bool | list[str] = False,
    roles: bool | list[str] = False,
    views: bool | list[str] = False,
    procedures: bool | list[str] = False,
    functions: bool | list[str] = False,
    triggers: bool | list[str] = False,
):
    # Note grants and rows are (currently) omitted. Rows should handled by tables being dropped.
    # Grants should be handled by everything else being dropped.
    from sqlalchemy_declarative_extensions.database.ddl import database_ddl
    from sqlalchemy_declarative_extensions.function.ddl import function_ddl
    from sqlalchemy_declarative_extensions.procedure.ddl import procedure_ddl
    from sqlalchemy_declarative_extensions.role.ddl import role_ddl
    from sqlalchemy_declarative_extensions.schema.ddl import schema_ddl
    from sqlalchemy_declarative_extensions.trigger.ddl import trigger_ddl
    from sqlalchemy_declarative_extensions.view.ddl import view_ddl

    concrete_schemas = metadata.info.get("schemas")
    concrete_roles = metadata.info.get("roles")
    concrete_views = metadata.info.get("views")
    concrete_procedures = metadata.info.get("procedures")
    concrete_functions = metadata.info.get("functions")
    concrete_triggers = metadata.info.get("triggers")
    concrete_databases = metadata.info.get("databases")

    if concrete_procedures and procedures:
        procedure_filter = procedures if isinstance(procedures, list) else None
        event.listen(
            metadata,
            "before_drop",
            procedure_ddl(concrete_procedures.are(), procedure_filter),
        )

    if concrete_triggers and triggers:
        trigger_filter = triggers if isinstance(triggers, list) else None
        event.listen(
            metadata,
            "before_drop",
            trigger_ddl(concrete_triggers.are(), trigger_filter),
        )

    if concrete_functions and functions:
        function_filter = functions if isinstance(functions, list) else None
        event.listen(
            metadata,
            "before_drop",
            function_ddl(concrete_functions.are(), function_filter),
        )

    if concrete_views and views:
        view_filter = views if isinstance(views, list) else None
        event.listen(
            metadata,
            "before_drop",
            view_ddl(concrete_views.are(), view_filter),
        )

    if concrete_schemas and schemas:
        schema_filter = schemas if isinstance(schemas, list) else None
        event.listen(
            metadata,
            "after_drop",
            schema_ddl(concrete_schemas.are(), schema_filter),
        )

    if concrete_roles and roles:
        role_filter = roles if isinstance(roles, list) else None
        event.listen(
            metadata,
            "after_drop",
            role_ddl(concrete_roles.are(), role_filter),
        )

    if concrete_databases and databases:
        database_filter = databases if isinstance(databases, list) else None
        event.listen(
            metadata,
            "after_drop",
            database_ddl(concrete_databases.are(), database_filter),
        )
