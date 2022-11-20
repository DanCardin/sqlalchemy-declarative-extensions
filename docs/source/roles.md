# Roles

Due to the inconsistent set of available options there are dialect-specific role
implementations. `Role` exists as a lowest common denominator, to create a role
without any dialect-specific options. For more complex roles, there exist alternative
implementations like `PGRole`.

```python
from sqlalchemy_declarative_extensions import PGRole, Roles

roles = Roles(ignore_roles=["user"]).are(
    "read",
    PGRole(
        "admin",
        login=True,
        superuser=False,
        createdb=True,
        inherit=True,
        createrole=True,
        replication=True,
        bypass_rls=True,
        in_roles=["read"],
    ),
)
```

```{eval-rst}
.. autoapimodule:: sqlalchemy_declarative_extensions.role.base
   :members:
```
