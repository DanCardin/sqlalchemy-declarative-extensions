# Roles

Due to the inconsistent set of available options there are dialect-specific role
implementations. [Role](generic.Role) exists as a lowest common denominator, to create a role
without any dialect-specific options. For more complex roles, there exist alternative
implementations like [Role](postgresql.Role).

```python
from sqlalchemy_declarative_extensions import Roles, Role

roles = Roles(ignore_roles=["user"]).are(
    "read",
    Role("admin", in_roles=["read"]),
)
```

```{eval-rst}
.. autoapimodule:: sqlalchemy_declarative_extensions.role.base
   :members: Roles, Role
   :noindex:
```
