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

## Example Usage

```python
from sqlalchemy import Column, types
from sqlalchemy.orm import as_declarative
from sqlalchemy_declarative_extensions import (
    declarative_database, Schemas, Roles, Role, Grants, PGGrant, Rows, Row
)

@declarative_database
@as_declarative
class Base:
    schemas = Schemas().are("example")
    roles = Roles(ignore_unspecified=True).are(
        PGRole("read", login=False),
        PGRole(
            "app",
            in_roles=['read']
        ),
    )
    grants = Grants().are(
        PGGrant("read").grant("select").default().on_tables_in_schema("public", 'example'),
        PGGrant("app").grant("insert", "update", "delete").default().on_tables_in_schema("public"),
    )
    rows = Rows().are(
        Row('foo', id=1),
    )


class Foo(Base):
    __tablename__ = 'foo'

    id = Column(types.Integer(), primary_key=True)
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

Currently, the set of supported declarative objects is essentially non-overlapping with
[Alembic-utils](https://github.com/olirice/alembic_utils). However in principle, there's
no reason that objects supported by this library couldn't begin to overlap (views, functions,
triggers); and one might begin to question when to use which library.

First, it's likely that this library can/should grow handlers for objects already supported by
alembic-utils. In particular, it's likely that any future support in this library for something
like a view could easily accept an `alembic_utils.pg_view.PGView` definition and handle it directly.
The two libraries are likely fairly complementary in that way, although it's important to note
some of the differences.

Alembic utils:

- Is more directly tied to Alembic and specifically provides functionality for autogenerating
  DDL for alembic, as the name might imply. It does **not** register into sqlalchemy's event
  system.
- Requires one to explicitly find/include the objects one wants to track with alembic.
- It provides direct translation of individual entities (like a single, specific `PGGrantTable`).
- In most cases, it appears to define a very "literal" interface (for example, `PGView` accepts
  the whole view definition as a raw literal string), rather than an abstracted one.

By contrast, this library:

- SqlAlchemy is the main dependency and registration point. The primary function of the library
  is to register into sqlalchemy's event system to ensure that a `metadata.create_all` performs
  the requisite statements to ensure the state of the database matches the declaration.

  This library does **not** require alembic, but it does (optionally) perform a similar function
  by way of enabling autogeneration support for non-native objects.

- Perhaps a technical detail, but this library registers the declaratively stated objects directly
  on the metadata/declarative-base. This allows the library to automatically know the intended
  state of the world, rather than needing to discover objects.
- The intended purpose of the supported objects is to declare what the state of the world **should**
  look like. Therefore the function of this library includes the (optional) **removal** of objects
  detected to exist which are not declared (much like alembic does for tables). Whereas alembic-utils
  only operates on objects you create entities for.
- As much as possible, this library provides more abstracted interfaces for defining objects.
  This is particularly important for objects like roles/grants where not every operation is a create
  or delete (in contrast to something like a view).
