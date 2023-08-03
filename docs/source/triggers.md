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

```{eval-rst}
.. autoapimodule:: sqlalchemy_declarative_extensions.trigger.base
   :members: Trigger, Triggers, register_trigger
```
