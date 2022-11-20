# Grants

Due to the inconsistent set of available options there are dialect-specific grant
options, there are currently **only** dialect-specific grant definition options.

```python
from sqlalchemy_declarative_extensions import Grants, PGGrant

grants = Grants().are(
    PGGrant("o2_read").grant("select").default().on_tables_in_schema("public"),
    PGGrant("o2_write")
    .grant("insert", "update", "delete")
    .default()
    .on_tables_in_schema("public"),
    PGGrant("o2_write").grant("usage").default().on_sequences_in_schema("public"),
)
```

Note, while we largely document the fluent style of grant creation, it is entirely
possible to create the underlying grants objects directly!

```{eval-rst}
.. autoapimodule:: sqlalchemy_declarative_extensions.grant.base
   :members:
```
