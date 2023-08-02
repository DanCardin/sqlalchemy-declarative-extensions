# SQLAlchemy

One can either register declared objects directly on a declarative base:

```python
# Using sqlalchemy's normal declarative base mechanism
from sqlalchemy.orm import declarative_base
from sqlalchemy_declarative_extensions import declarative_database

_Base = declarative_base()

@declarative_database
class Base(_Base):
    __abstract__ = True

    schemas = ...
    roles = ...

# Or using sqlalchemy's new decorator as of 1.4.
from sqlalchemy.orm import declarative_base
from sqlalchemy_declarative_extensions import as_declarative

@declarative_database
@as_declarative()
class Base(_Base):
    schemas = ...
    roles = ...
```

Or on the metadata directly, for example when not using the declarative style
API of SQLAlchemy.

```python
from sqlalchemy import MetaData
from sqlalchemy_declarative_extensions import declare_database

metadata = MetaData()

declare_database(
    metadata,
    schemas=...,
    roles=...,
)
```

## Event Registration

Additionally, you can opt into registration of sqlalchemy's creation-level
events, i.e. during a `metadata.create_all`.

```python
from sqlalchemy_declarative_extensions import register_sqlalchemy_events

register_sqlalchemy_events(schemas=True, roles=True, grants=True, rows=False)
```

Note, all available options are disabled by default! We assume this option will
most often be used in tests, where it's not clear that all options can be safely
used.
