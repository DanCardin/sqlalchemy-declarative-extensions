# MySQL

## Functions/Procedures

```python
from sqlalchemy_declarative_extensions import Functions, Procedures, Function, Procedure

functions = Functions().are(
     Function("some_function", "INSERT INTO foo"),
     ...
)
procedures = Procedures().are(
     Procedure("some_proc", "INSERT INTO foo"),
     ...
)
```

```{note}
Neither functions nor procedures currently support arguments!
```

While function/procedure **detailed** options do vary across dialects, it is possible to define
functions/procedures with all default options such that a generic implementation can be useful.

As such, the above example **does** use the generic instances, but a dialect-specific variant
subclass exists at `sqlalchemy_declarative_extensions.dialects.mysql`.

## Triggers

```python
from sqlalchemy_declarative_extensions import Triggers
from sqlalchemy_declarative_extensions.dialects.mysql import Trigger

triggers = Triggers().are(
     Trigger.before("insert", on="some_table", execute="SET NEW.value = NEW.value * 2")
     .named("before_insert_some_table")
     .follows("some_other_trigger")
)
```

Trigger options and semantics differ across the different dialects that support
them, which is the reason for the dialect-scoped `dialects.mysql` import above.

## API

```{eval-rst}
.. autoapimodule:: sqlalchemy_declarative_extensions.dialects.mysql
   :members: Function, FunctionSecurity, Procedure, ProcedureSecurity, FunctionSecurity, Trigger, TriggerTimes, TriggerForEach, TriggerEvents, TriggerOrders, TriggerOrder
```
