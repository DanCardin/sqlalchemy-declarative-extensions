# Grants

Due to the inconsistent set of available options there are dialect-specific grant
options, there are currently **only** dialect-specific grant definition options.

```python
from sqlalchemy_declarative_extensions import Grants
from sqlalchemy_declarative_extensions.dialects.postgresql import DefaultGrant

grants = Grants().are(
    DefaultGrant.on_tables_in_schema("public").grant("select", to="read"),
    DefaultGrant.on_tables_in_schema("public").grant("insert", "update", "delete", to="write"),
    DefaultGrant.on_sequences_in_schema("public").grant("usage", to="write"),
)
```

Note, while we largely document the fluent style of grant creation, it is entirely
possible to create the underlying grants objects directly!

```{eval-rst}
.. autoapimodule:: sqlalchemy_declarative_extensions.grant.base
   :members: Grants
```
