# SqlAlchemy Declarative Extensions

Adds extensions to SqlAlchemy (and/or Alembic) which allows declaratively
stating the existence of additional kinds of objects about your database
not natively supported by SqlAlchemy/Alembic.

This includes:

- Schemas
- Roles
- Privileges
- Models (i.e. data)

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
    declarative_database, Schemas, Roles, Role, Grants, for_role, Models, Model
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
        for_role("read").grant("select").default().on_tables_in_schema("public", 'example'),
        for_role("app").grant("insert", "update", "delete").default().on_tables_in_schema("public"),
    )
    models = Models().are(
        Model('foo', id=1),
    )


class Foo(Base):
    __tablename__ = 'foo'

    id = Column(types.Integer(), primary_key=True)
```

Note, there is also support for declaring objects directly through the `MetaData` for
users not using sqlalchemy's declarative API.

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
