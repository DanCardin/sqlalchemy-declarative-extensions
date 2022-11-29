# Roles

Due to the inconsistent set of available options there are dialect-specific role
implementations. `{ref}sqlalchemy_declarative_extensions.Role` exists as a lowest common denominator, to create a role
without any dialect-specific options. For more complex roles, there exist alternative
implementations like `{ref}sqlalchemy_declarative_extensions.dialects.postgresql.Role`.

```python
from sqlalchemy_declarative_extensions import Roles
from sqlalchemy_declarative_extensions.dialects.postgresql import Role

roles = Roles(ignore_roles=["user"]).are(
    "read",
    Role(
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
