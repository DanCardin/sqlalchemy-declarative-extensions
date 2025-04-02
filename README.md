# SQLAlchemy Declarative Extensions

[![Actions Status](https://github.com/DanCardin/sqlalchemy-declarative-extensions/actions/workflows/test.yml/badge.svg)](https://github.com/dancardin/sqlalchemy-declarative-extensions/actions)
[![codecov](https://codecov.io/gh/DanCardin/sqlalchemy-declarative-extensions/graph/badge.svg?token=DyS4xtntRo)](https://codecov.io/gh/DanCardin/sqlalchemy-declarative-extensions)
[![Documentation Status](https://readthedocs.org/projects/sqlalchemy-declarative-extensions/badge/?version=latest)](https://sqlalchemy-declarative-extensions.readthedocs.io/en/latest/?badge=latest)

See the full documentation
[here](https://sqlalchemy-declarative-extensions.readthedocs.io/en/latest/).

Adds extensions to SQLAlchemy (and/or Alembic) which allows declaratively
stating the existence of additional kinds of objects about your database not
natively supported by SQLAlchemy/Alembic.

The primary function(s) of this library include:

- Registering onto the SQLAlchemy event system such that `metadata.create_all`
  creates these objects.
- (Optionally) Registers into Alembic such that
  `alembic revision --autogenerate` automatically creates/updates/deletes
  declared objects.

Object support includes:

|                | Postgres | MySQL | SQLite | Snowflake |
| -------------- | -------- | ----- | ------ | --------- |
| Schemas        | ✓        | N/A   | ✓      | ✓         |
| Views          | ✓        | ✓     | ✓      | ✓         |
| Roles          | ✓        |       | N/A    | ✓         |
| Grants         | ✓        |       | N/A    |           |
| Default Grants | ✓        |       | N/A    |           |
| Functions      | ✓        | ✓     |        |           |
| Procedures     | ✓        | ✓     |        |           |
| Triggers       | ✓        | ✓     |        |           |
| Databases      | ✓        |       | N/A    | ✓         |
| Rows (data)    | ✓        | ✓     | ✓      | ✓         |
| "Audit Tables" | ✓        |       |        |           |

Notes:

- "Row" is implemented with pure SQLAlchemy concepts, so should work for any
  dialect that you can use SQLAlchemy to connect to.
- "Audit Tables" are a higher-level set of functions/triggers which record data
  changes against some source table.

In principle, this library **can** absolutely support any database supported by
SQLAlchemy, and capable of being introspected enough to support detection of
different kinds of objects. In reality, the existence of implementations are going to
be purely driven by actual usage/contributions/requests.

See [docs on dialect support](https://sqlalchemy-declarative-extensions.readthedocs.io/en/latest/contributing/dialect-support.html)
for information on how to improve support for a given dialect. Also feel free to submit an issue!

## Kitchen Sink Example (using all available features)

```python
from sqlalchemy import Column, types, select
from sqlalchemy.orm import as_declarative
from sqlalchemy_declarative_extensions import (
    declarative_database, Schemas, Roles, Row, View, view,
)
from sqlalchemy_declarative_extensions.dialects.postgresql import (
    DefaultGrant, Function, Trigger, Role
)
from sqlalchemy_declarative_extensions.audit import audit


@declarative_database
@as_declarative
class Base:
    # Note: each object type also has a plural version (i.e. Schemas/Roles/etc) where you can specify
    # collection-level options like `ignore_unspecified`).
    #
    # If you dont set any collection-level options, you can instead use raw list/iterable as the collection.
    schemas = Schemas().are("example")
    roles = Roles(ignore_unspecified=True).are(
        Role("read", login=False),
        Role(
            "app",
            in_roles=['read']
        ),
    )
    grants = [
        DefaultGrant.on_tables_in_schema("public", 'example').grant("select", to="read"),
        DefaultGrant.on_sequences_in_schema("public").grant("usage", to="read"),
        Grant.new("usage", to="read").on_schemas("example")
    ]
    rows = [
        Row('foo', id=1),
    ]
    views = [
        View("low_foo", "select * from foo where i < 10"),
    ]
    functions = [
        Function(
            "fancy_function",
            """
            BEGIN
            INSERT INTO foo (id) select NEW.id + 1;
            RETURN NULL;
            END
            """,
            language="plpgsql",
            returns="trigger",
        ),
    ]
    triggers = [
        Trigger.after("insert", on="foo", execute="fancy_function")
        .named("on_insert_foo")
        .when("pg_trigger_depth() < 1")
        .for_each_row(),
    ]


@audit()
class Foo(Base):
    __tablename__ = 'foo'

    id = Column(types.Integer(), primary_key=True)


audit_table = Foo.__audit_table__


@view(Base)
class HighFoo:
    __tablename__ = "high_foo"
    __view__ = select(Foo.__table__).where(Foo.__table__.c.id >= 10)
```

Note, there is also support for declaring objects directly through the
`MetaData` for users not using sqlalchemy's declarative API.

## Event Registration

By default, the above example does not automatically do anything. Depending on
the context, you can use one of two registration hooks:
`register_sqlalchemy_events` or `register_alembic_events`.

### `register_sqlalchemy_events`

This registers events in SQLAlchemy's event system such that a
`metadata.create_all(...)` call will create the declared database objects.

```python
from sqlalchemy_declarative_extensions import register_sqlalchemy_events

metadata = Base.metadata  # Given the example above.
register_sqlalchemy_events(metadata)
# Which is equivalent to...
register_sqlalchemy_events(metadata, schemas=False, roles=False, grants=False, rows=False)
```

All object types are opt in, and should be explicitly included in order to get
registered.

Practically, this is to avoid issues with testing. In **most** cases the
`metadata.create_all` call will be run in tests, a context where it's more
likely that you dont **need** grants or grants, and where parallel test
execution could lead to issues with role or schema creation, depending on your
setup.

### `register_alembic_events`

This registers comparators in Alembic's registration system such that an
`alembic revision --autogenerate` command will diff the existing database state
against the declared database objects, and issue statements to
create/update/delete objects in order to match the declared state.

```python
# alembic's `env.py`
from sqlalchemy_declarative_extensions import register_alembic_events

register_alembic_events()
# Which is equivalent to...
register_sqlalchemy_events(schemas=True, roles=True, grants=True, rows=True)
```

All object types are opt out but can be excluded.

In contrast to `register_sqlalchemy_events`, it's much more likely that you're
declaring most of these object types in order to have alembic track them

## Alembic-utils

[Alembic Utils](https://github.com/olirice/alembic_utils) is the primary library
against which this library can be compared. At time of writing, **most** (but
not all) object types supported by alembic-utils are supported by this library.
One might begin to question when to use which library.

Below is a list of points on which the two libraries diverge. But note that you
**can** certainly use both in tandem! It doesn't need to be one or the other,
and certainly for any object types which do not overlap, you might **need** to
use both.

- Database Support

  - Alembic Utils seems to explicitly only support PostgreSQL.

  - This library is designed to support any dialect (in theory). Certainly
    PostgreSQL is **best** supported, but there does exist support for specific
    kinds of objects to varying levels of support for Snowflake, SQLite, and MySQL,
    so far.

- Architecture

  - Alembic Utils is directly tied to Alembic and does not support SQLAlchemy's
    `MetaData.create_all`. It's also the responsibility of the user to
    discover/register objects in alembic.

  - This library **depends** only on SQLAlchemy, although it also supports
    alembic. Support for `MetaData.create_all` can be important for creating all
    object types in tests. It also is designed such that objects are registered
    on the `MetaData` itself, so there is no need for any specific discovery
    phase.

- Scope

  - Alembic Utils declares specific, individual objects. I.e. you instantiate
    one specific `PGGrantTable` or `PGView` instance and Alembic know knows you
    want that object to be created. It cannot drop objects it is not already
    aware of.

  - This library declares the objects the system as a whole expects to exist.
    Similar to Alembic's behavior on tables, it will (by default) detect any
    **undeclared** objects that should not exist and drop them. That means, you
    can rely on this object to ensure the state of your migrations matches the
    state of your database exactly.

- Migration history

  - Alembic Utils imports and references its own objects in your migrations
    history. This can be unfortunate, in that it deeply ties your migrations
    history to alembic-utils.

    (In fact, this can be a sticking point, trying to convert **away** from
    `alembic_utils`, because it will attempt to drop all the (e.g `PGView`)
    instances previously created when we replaced it with this library.)

  - This library, by contrast, prefers to emit the raw SQL of the operation into
    your migration. That means you know the exact commands that will execute in
    your migration, which can be helpful in debugging failure. It also means, if
    at any point you decide to stop use of the library (or pause a given type of
    object, due to a bug), you can! This library's behaviors are primarily very
    much `--autogenerate`-time only.

- Abstraction Level

  - Alembic Utils appears to define a very "literal" interface (for example,
    `PGView` accepts the whole view definition as a raw literal string).

  - This library tries to, as much as possible, provide a more abstracted
    interface that enables more compatibility with SQLAlchemy (For example
    `View` accepts SQLAlchemy objects which can be coerced into a `SELECT`). It
    also tends towards "builder" interfaces which progressively produce a object
    (Take a look at the `DefaultGrant` above, for an example of where that's
    helpful).

A separate note on conversion/compatibility. Where possible, this library tries
to support alembic-utils native objects as stand-ins for the objects defined in
this library. For example, `alembic_utils.pg_view.PGView` can be declared
instead of a `sqlalchemy_declarative_extensions.View`, and we will internally
coerce it into the appropriate type. Hopefully this eases any transitional
costs, or issues using one or the other library.
