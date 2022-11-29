from __future__ import annotations

from typing import Any, Callable, Iterable, Optional, Type, TYPE_CHECKING, Union

from sqlalchemy import event
from sqlalchemy.orm import DeclarativeMeta
from sqlalchemy.sql.schema import MetaData

from sqlalchemy_declarative_extensions.grant.base import Grants
from sqlalchemy_declarative_extensions.grant.ddl import grant_ddl
from sqlalchemy_declarative_extensions.role.base import Roles
from sqlalchemy_declarative_extensions.role.ddl import role_ddl
from sqlalchemy_declarative_extensions.row.base import Row, Rows
from sqlalchemy_declarative_extensions.row.query import rows_query
from sqlalchemy_declarative_extensions.schema.base import Schemas
from sqlalchemy_declarative_extensions.schema.ddl import schema_ddl

if TYPE_CHECKING:
    from sqlalchemy_declarative_extensions.grant.base import G
    from sqlalchemy_declarative_extensions.role.base import R_unknown
    from sqlalchemy_declarative_extensions.schema.base import Schema


def declarative_database(
    base: Optional[Any] = None,
) -> Union[
    Type[DeclarativeMeta], Callable[[Type[DeclarativeMeta]], Type[DeclarativeMeta]]
]:
    """Decorate a SQLAlchemy declarative base object to register database objects.

    See also :func:`sqlalchemy_declarative_extensions.declare_database`, of which this decorator is syntactic sugar.

    By decorating your declarative base with this decorator, the attributes
    "schemas", "roles", and "grants" are read and will register with SQLAlchemy
    and/or Alembic to ensure they're created during a ``metadata.create_createall``
    call or ``alembic --autogenerate``.

    Examples:
        >>> from sqlalchemy.orm import declarative_base
        >>> Base_ = declarative_base()
        >>>
        >>> from sqlalchemy_declarative_extensions import declarative_database, Roles
        >>> from sqlalchemy_declarative_extensions.dialects.postgresql import Role
        >>> @declarative_database
        ... class Base(Base_):
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

    def _declare_database(cls: Type[DeclarativeMeta]) -> Type[DeclarativeMeta]:
        raw_roles = getattr(cls, "roles", None)
        raw_schemas = getattr(cls, "schemas", None)
        raw_grants = getattr(cls, "grants", None)
        raw_rows = getattr(cls, "rows", None)

        declare_database(
            cls.metadata,
            schemas=raw_schemas,
            roles=raw_roles,
            grants=raw_grants,
            rows=raw_rows,
        )
        return cls

    if base is None:
        return _declare_database
    return _declare_database(base)


def declare_database(
    metadata: MetaData,
    *,
    schemas: Union[None, Iterable[Union[Schema, str]], Schemas] = None,
    roles: Union[None, Iterable[R_unknown], Roles] = None,
    grants: Union[None, Iterable[G], Grants] = None,
    rows: Union[None, Iterable[Row], Rows] = None,
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
        rows: The set of rows to ensure are applied to the roles/schemas/tables.
    """
    metadata.info["schemas"] = Schemas.coerce_from_unknown(schemas)
    metadata.info["roles"] = Roles.coerce_from_unknown(roles)
    metadata.info["grants"] = Grants.coerce_from_unknown(grants)
    metadata.info["rows"] = Rows.coerce_from_unknown(rows)


def register_sqlalchemy_events(
    maybe_metadata: MetaData | DeclarativeMeta,
    schemas=False,
    roles=False,
    grants=False,
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
    if isinstance(maybe_metadata, MetaData):
        metadata = maybe_metadata
    else:
        metadata = maybe_metadata.metadata

    concrete_schemas = metadata.info["schemas"]
    concrete_roles = metadata.info["roles"]
    concrete_grants = metadata.info["grants"]
    concrete_rows = metadata.info["rows"]

    if concrete_schemas and schemas:
        for schema in concrete_schemas:
            event.listen(
                metadata,
                "before_create",
                schema_ddl(schema),
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

    if concrete_rows and rows:
        event.listen(
            metadata,
            "after_create",
            rows_query(concrete_rows),
        )
