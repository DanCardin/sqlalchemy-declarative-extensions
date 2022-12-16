# SqlAlchemy Declarative Extensions

[![Actions Status](https://github.com/dancardin/sqlalchemy-declarative-extensions/workflows/test/badge.svg)](https://github.com/dancardin/sqlalchemy-declarative-extensions/actions) [![Coverage Status](https://coveralls.io/repos/github/DanCardin/sqlalchemy-declarative-extensions/badge.svg?branch=main)](https://coveralls.io/github/DanCardin/sqlalchemy-declarative-extensions?branch=main) [![Documentation Status](https://readthedocs.org/projects/sqlalchemy-declarative-extensions/badge/?version=latest)](https://sqlalchemy-declarative-extensions.readthedocs.io/en/latest/?badge=latest)

See the full documentation [here](https://sqlalchemy-declarative-extensions.readthedocs.io/en/latest/).

Adds extensions to SqlAlchemy (and/or Alembic) which allows declaratively
stating the existence of additional kinds of objects about your database
not natively supported by SqlAlchemy/Alembic.

This includes:

- Schemas
- Roles
- Privileges
- Rows (i.e. data)

The primary function(s) of this library include:

- Registering onto the SqlAlchemy event system such that `metadata.create_all`
  creates these objects.
- (Optionally) Registers into Alembic such that `alembic revision --autogenerate`
  automatically creates/updates/deletes declared objects.

## Kitchen Sink Example Usage

```python
from sqlalchemy import Column, types, select
from sqlalchemy.orm import as_declarative
from sqlalchemy_declarative_extensions import (
    declarative_database, Schemas, Roles, Grants, Rows, Row, Views, View, view
)
from sqlalchemy_declarative_extensions.dialects.postgresql import DefaultGrant, Role


@declarative_database
@as_declarative
class Base:
    schemas = Schemas().are("example")
    roles = Roles(ignore_unspecified=True).are(
        Role("read", login=False),
        Role(
            "app",
            in_roles=['read']
        ),
    )
    grants = Grants().are(
        DefaultGrant.on_tables_in_schema("public", 'example').grant("select", to="read"),
        DefaultGrant.on_tables_in_schema("public").grant("insert", "update", "delete", to="write"),
        DefaultGrant.on_sequences_in_schema("public").grant("usage", to="write"),
    )
    rows = Rows().are(
        Row('foo', id=1),
    )
    views = Views().are(View("low_foo", "select * from foo where i < 10"))


class Foo(Base):
    __tablename__ = 'foo'

    id = Column(types.Integer(), primary_key=True)


@view(Base)
class HighFoo:
    __tablename__ = "high_foo"
    __view__ = select(Foo.__table__).where(Foo.__table__.c.id >= 10)
```

Note, there is also support for declaring objects directly through the `MetaData` for
users not using sqlalchemy's declarative API.

## Event Registration

By default, the above example does not automatically do anything. Depending on the context,
you can use one of two registration hooks: `register_sqlalchemy_events` or `register_alembic_events`.

### `register_sqlalchemy_events`

This registers events in SqlAlchemy's event system such that a `metadata.create_all(...)` call
will create the declared database objects.

```python
from sqlalchemy_declarative_extensions import register_sqlalchemy_events

metadata = Base.metadata  # Given the example above.
register_sqlalchemy_events(metadata)
# Which is equivalent to...
register_sqlalchemy_events(metadata, schemas=False, roles=False, grants=False, rows=False)
```

All object types are opt in, and should be explicitly included in order to get registered.

Practically, this is to avoid issues with testing. In **most** cases the `metadata.create_all` call
will be run in tests, a context where it's more likely that you dont **need** grants or grants,
and where parallel test execution could lead to issues with role or schema creation, depending
on your setup.

### `register_alembic_events`

This registers comparators in Alembic's registration system such that an `alembic revision --autogenerate`
command will diff the existing database state against the declared database objects, and issue
statements to create/update/delete objects in order to match the declared state.

```python
# alembic's `env.py`
from sqlalchemy_declarative_extensions import register_alembic_events

register_alembic_events()
# Which is equivalent to...
register_sqlalchemy_events(schemas=True, roles=True, grants=True, rows=True)
```

All object types are opt out but can be excluded.

In contrast to `register_sqlalchemy_events`, it's much more likely that you're declaring most of these
object types in order to have alembic track them

## Database support

In principle, this library **can** absolutely support any database supported by SqlAlchemy,
and capable of being introspected enough to support detection of different kinds of objects.

In reality, the implementations are going to be purely driven by actual usage. The
current maintainer(s) primarily use PostgreSQL and as such individual features for
other databases will either suffer or lack implementation.

As much as possible, objects will be defined in a database-agnostic way, and the comparison
infrastructure should be the sole difference. However databases engines are not the same, and
certain kinds of objects, like GRANTs, are inherently database engine specific, and there's
not much common ground between a PostgreSQL grant and a MySQL one. As such, they will
include database specific objects.

## Alembic-utils

Currently, the set of supported declarative objects is largely non-overlapping with
[Alembic-utils](https://github.com/olirice/alembic_utils). However in principle, there's
no reason that objects supported by this library couldn't begin to overlap (functions,
triggers); and one might begin to question when to use which library.

Note that where possible this library tries to support alembic-utils native objects
as stand-ins for the objects defined in this library. For example, `alembic_utils.pg_view.PGView`
can be declared instead of a `sqlalchemy_declarative_extensions.View`, and we will internally
coerce it into the appropriate type. Hopefully this eases any transitional costs, or
issues using one or the other library.

Alembic utils:

1. Is more directly tied to Alembic and specifically provides functionality for autogenerating
   DDL for alembic, as the name might imply. It does **not** register into sqlalchemy's event
   system.

2. Requires one to explicitly find/include the objects one wants to track with alembic.

3. Declares single, specific object instances (like a single, specific `PGGrantTable`). This
   has the side-effect that it can only track included objects. It cannot, for example,
   remove objects which should not exist due to their omission.

4. In most cases, it appears to define a very "literal" interface (for example, `PGView` accepts
   the whole view definition as a raw literal string), rather than attempting to either abstract
   the objects or accept abstracted (like a `select` object) definition.

5. Appears to only be interested in supporting PostgreSQL.

By contrast, this library:

1. SqlAlchemy is the main dependency and registration point (Alembic is, in fact, an optional dependency).
   The primary function of the library is to declare the underlying objects. And then registration into
   sqlalchemy's event system, or registration into alembic's detection system are both optional features.

2. Perhaps a technical detail, but this library registers the declaratively stated objects directly
   on the metadata/declarative-base. This allows the library to automatically know the intended
   state of the world, rather than needing to discover objects.

3. The intended purpose of the supported objects is to declare what the state of the world **should**
   look like. Therefore the function of this library includes the (optional) **removal** of objects
   detected to exist which are not declared (much like alembic does for tables).

4. As much as possible, this library provides more abstracted interfaces for defining objects.
   This is particularly important for objects like roles/grants where not every operation is a create
   or delete (in contrast to something like a view), where a raw SQL string makes it impossible to
   diff two different a-like objects.

5. Tries to define functionality in cross-dialect terms and only where required farm details out to
   dialect-specific handlers. Not to claim that all dialects are treated equally (currently only
   PostgreSQL has first-class support), but technically, there should be no reason we wouldn't support
   any supportable dialect. Today SQLite (for whatever that's worth), and MySQL have **some** level
   of support.
