# Functions

```python
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base
from sqlalchemy_declarative_extensions import declarative_database, Function, Functions

_Base = declarative_base()


@declarative_database
class Base(_Base):
    __abstract__ = True

    functions = Functions().are(
        Function("gimme", "SELECT 1;", returns="INTEGER"),
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
```

```{note}
Functions options are wildly different across dialects. As such, you should likely always use
the diaelect-specific `Function` object.
```

```{note}
Function behavior (for eaxmple...arguments) is not fully implemented at current time,
although it **should** be functional for the options it does support. Any ability to instantiate
an object which produces a syntax error should be considered a bug. Additionally, feature requests
for supporting more function options are welcome!

In particular, the current function support is heavily oriented around support for defining triggers.
```

```{eval-rst}
.. autoapimodule:: sqlalchemy_declarative_extensions.function.base
   :members: Functions, Function, register_function
```
