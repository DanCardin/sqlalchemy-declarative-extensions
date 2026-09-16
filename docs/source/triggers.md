# Triggers

```python
from sqlalchemy.orm import declarative_base
from sqlalchemy_declarative_extensions import declarative_database, Function, Functions, Triggers
from sqlalchemy_declarative_extensions.dialects.postgresql import Trigger

_Base = declarative_base()


@declarative_database
class Base(_Base):
    __abstract__ = True

    functions = Functions().are(
        Function(
            "fancy_trigger",
            """
            BEGIN
            INSERT INTO foo (id) select NEW.id + 1;
            RETURN NULL;
            END
            """,
            language="plpgsql",
            returns="trigger",
        )
    )

    triggers = Triggers().are(
        Trigger.after("insert", on="foo", execute="fancy_trigger")
        .named("on_insert_foo")
        .when("pg_trigger_depth() < 1")
        .for_each_row(),
    )
```

```{note}
Triggers options are wildly different across dialects. As such, you should always use
the dialect-specific `sqlalchemy_declarative_extensions.trigger.base.Trigger` subclasses.
```

```{note}
Trigger behavior not fully implemented at current time, although it **should** be functional for
the options it does support. Any ability to instantiate an object which produces a syntax error
should be considered a bug. Additionally, feature requests for supporting more trigger options
are welcome!
```

## Table-level triggers

Unlike most other object types, a trigger always targets exactly one table. It can
therefore be declared inline on that table instead, through `__table_args__` (or the
positional arguments of a [Table](sqlalchemy.schema.Table)), in the same way you would
declare an `Index` or `UniqueConstraint`.

```python
from sqlalchemy import Column, types
from sqlalchemy_declarative_extensions.dialects.postgresql import Trigger


class Foo(Base):
    __tablename__ = "foo"
    __table_args__ = (
        Trigger.after("insert", execute="fancy_trigger")
        .named("on_insert_foo")
        .when("pg_trigger_depth() < 1")
        .for_each_row(),
    )

    id = Column(types.Integer(), primary_key=True)
```

Declared this way, `on` is inferred from the table being attached to (schema-qualified,
where that table declares a non-default schema), and need not be supplied. Supplying an
`on` which disagrees with that table is an error.

The resulting trigger is registered against the same `MetaData` as one declared through
`Triggers`, so the two styles can be freely mixed, and both are picked up by alembic
autogeneration. The trigger object itself is not mutated by being attached, so a single
definition can be shared among multiple tables.

```{note}
`name`, unlike `on`, is **not** inferred. A trigger attached to a table must be given one,
either through `name=` or `.named(...)`, else a `ValueError` is raised at declaration time.
```

```{note}
The `MetaData` must have been set up (i.e. `declarative_database` applied, or
`declare_database` called) **before** the models which attach triggers are defined. This is
the natural ordering, but it does mean that doing so afterwards will discard any
already-attached table-level triggers.
```

```{eval-rst}
.. autoapimodule:: sqlalchemy_declarative_extensions.trigger.base
   :members: Trigger, Triggers, register_trigger
```
