# Dialect Support

Below, you will see that for any **preexisting feature**, there are predefined
locations in the code where it is straightforward to slot in the implementation
required to introspect the data required to implement that "feature".

That is to say, if `foo` dialect is missing some internal `get_schemas` API,
required to use the `Schemas` feature, then a contributor need only implement
`get_schemas` in order to enable that feature for the `foo` dialect.

## Dialect Organization

The library source intentionally separates the implementation of "support"
(comparison/autogeneration) for a given database feature (i.e. Views, Grants,
etc), from the dialect-specific definitions of those objects and specific
queries for how to introspect them.

Generic feature implementation lives under
`src/sqlalchemy_declarative_extensions/<feature-name>/`, where "<feature-name>"
would be something like "view", "grant", or "role".

The dialect-specific versions of any objects, schema definitions, and queries
live under `src/sqlalchemy_declarative_extensions/dialects/<dialect>/`; where
"<dialect>" should correspond to the name of the sqlalchemy dialect (i.e.
"postgresql", "mysql", etc)

## Generic `query.py`

If you first navigate to
`src/sqlalchemy_declarative_extensions/dialects/query.py`, you will see a
central listing of all exposed "generic" functions, which are dispatched to
based on the features that dialect implements.

Here's an excerpt for example:

```python
from sqlalchemy_declarative_extensions.dialects.mysql.query import (
    check_schema_exists_mysql,
)
from sqlalchemy_declarative_extensions.dialects.postgresql.query import (
    check_schema_exists_postgresql,
)
from sqlalchemy_declarative_extensions.dialects.sqlite.query import (
    check_schema_exists_sqlite,
)
from sqlalchemy_declarative_extensions.sqlalchemy import dialect_dispatch

check_schema_exists = dialect_dispatch(
    postgresql=check_schema_exists_postgresql,
    sqlite=check_schema_exists_sqlite,
    mysql=check_schema_exists_mysql,
)
```

"Feature" implementations should only reference **these** functions, which will
in turn, dispatch to the dialect-specific versions, based on the current
connection's dialect.

If a given function is missing a dispatch target for a given dialect, it will
raise an error and say so at runtime. Effectively, lack of dispatch
implementations imply lack of support for a given "feature" generally.

For contributors, this means encountering one such error for a dialect leaves a
very specifically shaped contribution point for you to add support for
preexisting features!

Within that folder, the general pattern is thus:

```
exampledialect/
    __init__.py
    query.py
    schema.py
    <feature>.py
```

## Dialect-specific `query.py`

Given that i.e. `postgresql.query.get_schemas_postgresql` is directly referenced
within the generic `query.py`, the dialect-specific `query.py` is the next
obvious place to look.

Lets look at what this might look like for Postgres:

```python
from sqlalchemy.engine import Connection

from sqlalchemy_declarative_extensions.dialects.postgresql.schema import schemas_query
from sqlalchemy_declarative_extensions.schema.base import Schema


def get_schemas_postgresql(connection: Connection):
    return {Schema(schema) for schema, *_ in connection.execute(schemas_query).fetchall()}
```

Essentially, the job of each dispatch function is to produce the given kind of
object being referenced by the dispatch function, in this case a `List[Schema]`.

```{note}
Schema is a very simple case, without any dialect specific variants.

For something more complex, such as a "view" or a "grant", you would instead produce
dialect-specific variants.

If that dialect-specific variant does not exist, then it would be a prerequisite for
implementing that feature to the fullest extent.
```

## Dialect-specific `schema.py`

Above, you'll notice `schemas_query` being referenced from the `schema.py`
module, rather than the query being directly embedded in the function. While
this isn't strictly necessary, it helps decouple the "business logic" of these
functions from the queries required to introspect the data in the first place.

Additionally it assists in reference-table reuse, for example with databases
like Postgres, who's queries frequently reference tables like
`pg_class`/`pg_namespace` in the implementations of many of the features.

Continuing the previous example, Postgres' `schema.py` might look like

```python
from sqlalchemy import column, table
from sqlalchemy_declarative_extensions.sqlalchemy import select


pg_namespace = table(
    "pg_namespace",
    column("oid"),
    column("nspname"),
    column("nspowner"),
    column("nspacl"),
)

schemas_query = (
    select(pg_namespace.c.nspname)
    .where(column != "information_schema")
    .where(column.notlike("pg_%"))
    .where(pg_namespace.c.nspname != "public")
)
```

We use SQLAlechemy's lightweight `table`/`column` syntax for describing the
minimal set of columns we need on each `pg_` (in Postgres' case) table, in order
to describe each required query.

Helpfully, this also allows us to use `bindparam` for certain functions which
need to parametrize the query being performed.

## Finished?

For a simple feature like schemas, yes!(?) The current implementation of
`Schemas`/`Schema` support **only** references the `get_schemas` dispatcher, so
some net-new dialect would be done at this point, in order to implement that
feature for this library.

As mentioned above, features like "view", "grant", "role", etc (most other
features to be honest) are more complex and frequetntly require more specialized
dialect-specific versions of the generic type in order to function against that
dialect.

However even then, describing the domain-object as a "comparable" `dataclass` is
most of the battle. Once you have a type that can be compared with other types
of the same dialect (and which knows how to produce dialect-appropriate SQL),
most of the existing machinery for the above features will kick in and support
**should** be automatic.

## New "features"

Adding new features are whole separate thing...left mostly undocumented for now.
Referencing the existing features' implementions is probably the best way to go
about adding a new "feature".
