# Views

Views definition and registration can be performed exactly as it is done with other object
types, by defining the set of views on the `MetaData` or declarative base, like so:

```python
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_declarative_extensions import declarative_database, View, Views

_Base = declarative_base()


@declarative_database()
class Base(_Base):
    __abstract__ = True

    views = Views().are(
        View("foo", "select * from bar where id > 10", schema="baz"),
    )
```

And if you want to define views using raw strings, or otherwise not reference the tables
produced off the `MetaData`, then this is absolutely a valid way to organize.

## The `view` decorator

However views differ from most of the other object types, in that they are convenient to
define **in terms of** the tables they reference (i.e. your existing set of models/tables).
In fact personally, all of my views are produced from [select](sqlalchemy.sql.expression.select) expressions
referencing the underlying [Table](sqlalchemy.schema.Table) object.

This commonly introduce a circular reference problem wherein your tables/models are defined
through subclassing the declarative base, which means your declarative base cannot then
have the views statically defined **on** the base (while simultaneously referencing those models).

```{note}
There are ways of working around this in SQLAlchemy-land. For example by creating a ``MetaData``
ahead of time and defining all models in terms of their underlying ``Table``.

Or perhaps by using SQLAlchemy's mapper apis such that you're not subclassing the declarative base
for models.

In any case, these options are more complex and probably atypical. As such, we cannot assume
you will adopt them.
```

For everyone else, the [view](sqlalchemy_declarative_extensions.view) decorator is meant to be the
solution to that problem.

This strategy allows one to organize their views alongside the models/tables those
views happen to be referencing, without requiring the view be importable at MetaData/model base
definition time.

### Option 1

```python
from sqlalchemy import Column, types, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_declarative_extensions import view

Base = declarative_base()


class Foo(Base):
    __tablename__ = 'foo'

    id = Column(types.Integer, primary_key=True)


@view()
class Bar1(Base):
    __tablename__ = 'bar'
    __view__ = select(Foo.__table__).where(Foo.__table__.id > 10)

    id = Column(types.Integer, primary_key=True)
```

The primary difference between Options 1 and 2 in the above example is of how the
resulting classes are seen by SQLAlchemy/Alembic natively.

In the case of `Bar1`, SQLAlchemy/Alembic actually think that class is a normal table.
Therefore querying the view looks identical to a real table: `session.query(Bar1).all()`

For alembic, this means that alembic thinks you defined a table and will attempt to
autogenerate it (while this library will also notice it and attempt to autogenerate
a conflicting view.

In order to use this option, we suggest you use one or both of some utility functions provided
under the `sqlalchemy_declarative_extensions.alembic`: [ignore_view_tables](sqlalchemy_declarative_extensions.alembic.ignore_view_tables)
and [compose_include_object_callbacks](sqlalchemy_declarative_extensions.alembic.compose_include_object_callbacks).

Somewhere in your Alembic `env.py`, you will have a block which looks like this:

```python
with connectable.connect() as connection:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        ...
    )
```

The above call to `configure` accepts an `include_object`, which tells alembic to include or ignore
all detected objects.

```python
from sqlalchemy_declarative_extensions.alembic import ignore_view_tables
...
context.configure(..., include_object=ignore_view_tables)
```

If you happen to already be using `include_object` to perform filtering, we provide an additional
utility to more easily compose our version with your own. Although you can certainly manually call
`ignore_view_tables` directly, yourself.

```python
from sqlalchemy_declarative_extensions.alembic import ignore_view_tables, compose_include_object_callbacks
...
def my_include_object(object, *_):
    if object.name != 'foo':
        return True
    return False

context.configure(..., include_object=compose_include_object_callbacks(my_include_object, ignore_view_tables))
```

## Option 2

```python
from sqlalchemy import Column, types, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_declarative_extensions import view

Base = declarative_base()


class Foo(Base):
    __tablename__ = 'foo'

    id = Column(types.Integer, primary_key=True)


@view(Base)  # or `@view(Base.metadata)`
class Bar2:
    __tablename__ = 'bar'
    __view__ = select(Foo.__table__).where(Foo.__table__.id > 10)
```

By contrast, with Option 2, your class is not subclassing `Base`, therefore it's
not registered as a real table by SQLAlchemy or Alembic. There's no additional
work required to get them to ignore the table, because it's not one.

Unfortunately, that means you cannot **invisibly** treat it as though it's a normal model,
largely because it doesn't have the columns enumerated out in the same way.

However we can provide some basic support for treating it as a table as far as the ORM is concerned.
For example, you can still `session.query(Bar2).all()` directly.

However, in most cases views primarily benefit non-code consumers of the database, because there's
no practical difference between querying a literal view, versus executing the underlying query
of that view, through something like `session.execute(Bar2.__view__)`.
