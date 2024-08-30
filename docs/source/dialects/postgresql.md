# Postgresql

The primary objects of interest are
[Role](sqlalchemy_declarative_extensions.dialects.postgresql.role.Role), and
[DefaultGrant](sqlalchemy_declarative_extensions.dialects.postgresql.grant.DefaultGrant)
(all other objects are support types which comprise these objects or else types
which these objects produce).

## Role

```python
from sqlalchemy_declarative_extensions import Roles
from sqlalchemy_declarative_extensions.dialects.postgresql import Role

roles = Roles().are(Role('foo'), Role('bar', login=True), ...)
```

Define roles with Postgres-specific options

## Grant

```python
from sqlalchemy_declarative_extensions import Grants
from sqlalchemy_declarative_extensions.dialects.postgresql import DefaultGrant

grants = Grants().are(DefaultGrant.on_table_in_schema('public').grant('select', to='foo'), ...)
```

Define postgres grants. Note there is not currently a generic grant option, due
to wild differences in details/semantics across dialects.

Note, [DefaultGrant](DefaultGrant) is most likely the intended object to make
use of when declaring most grants. A vanilla [Grant](Grant) **may** encounter
problems with the provenance of the objects it references (i.e. a defined
`Grant` may be evaluated before the objects the grant references exist).

In comparison, a `DefaultGrant` generally implies the absolute set of grants one
wants to exist in general and a `DefaultGrant` will, by default, project the
implied grants against pre-existing objects and ensure they have the same sets
of permissions.

## Functions

There currently exists a generic `Function` object which contains all function
behavior. Note that there **do** exist certain function definition options which
are specific to Postgres, and should they be implemented you would be required
to shift use to the dialect-specific version.

Additionally, not all function options are currently supported for Postgres. At
current moment, only the options required to support the
[Audit Table](../audit_tables.md) feature have been implemented.

## Triggers

```python
from sqlalchemy_declarative_extensions import Triggers
from sqlalchemy_declarative_extensions.dialects.postgresql import Trigger

triggers = Triggers().are(
     Trigger.after("insert", on="foo", execute="gimme")
     .named("on_insert_foo")
     .when("pg_trigger_depth() < 1")
     .for_each_row()
     .with_arguments(["arg1", "arg2"]),
)
```

Trigger options and semantics differ across the different dialects that support
them. In particular the [TriggerTimes](TriggerTimes),
[TriggerForEach](TriggerForEach), and [TriggerEvents](TriggerEvents) options are
all Postgres-specific.

Additionally, not all trigger options are currently supported for Postgres. At
current moment, only the options required to support the
[Audit Table](../audit_tables.md) feature as well as basic support for arguments
have been implemented.

## API

```{eval-rst}
.. autoapimodule:: sqlalchemy_declarative_extensions.dialects.postgresql.role
   :members: Role
```

```{eval-rst}
.. autoapimodule:: sqlalchemy_declarative_extensions.dialects.postgresql.grant
   :members:
```

```{eval-rst}
.. autoapimodule:: sqlalchemy_declarative_extensions.dialects.postgresql.grant_type
   :members:
```

```{eval-rst}
.. autoapimodule:: sqlalchemy_declarative_extensions.dialects.postgresql
   :members: TriggerTimes, TriggerForEach, TriggerEvents, Trigger
```
