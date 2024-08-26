# MySQL

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
   :members: Trigger, TriggerTimes, TriggerForEach, TriggerEvents, TriggerOrders, TriggerOrder
```
