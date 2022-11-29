# Postgresql

The primary objects of interest are [Role](postgresql.Role), and [DefaultGrant](DefaultGrant) (all
other objects are support types which comprise these objects or else types which
these objects produce).

## Role

```python
from sqlalchemy_declarative_extensions import Roles
from sqlalchemy_declarative_extensions.dialects.postgresql import Role

roles = Roles().are(Role('foo'), Role('bar', login=True), ...)
```

Define roles with Postgres-specific options

```{eval-rst}
.. autoapimodule:: sqlalchemy_declarative_extensions.dialects.postgresql
   :members: Role
```

## Grant

```python
from sqlalchemy_declarative_extensions import Grants
from sqlalchemy_declarative_extensions.dialects.postgresql import DefaultGrant

grants = Grants().are(DefaultGrant.on_table_in_schema('public').grant('select', to='foo'), ...)
```

Define postgres grants. Note there is not currently a generic grant option, due
to wild differences in details/semantics across dialects.

Note, [DefaultGrant](DefaultGrant) is most likely the intended object to make use of when
declarting most grants. A vanilla [Grant](Grant) **may** encounter problems with the provenance
of the objects it references (i.e. a defined `Grant` may be evaluated before the objects
the grant references exist).

In comparison, a `DefaultGrant` generally implies the absolute set of grants one wants
to exist in general and a `DefaultGrant` will, by default, project the implied grants
against pre-existing objects and ensure they have the same sets of permissions.

```{eval-rst}
.. autoapimodule:: sqlalchemy_declarative_extensions.dialects.postgresql.grant
   :members:
```

```{eval-rst}
.. autoapimodule:: sqlalchemy_declarative_extensions.dialects.postgresql.grant_type
   :members:
```
