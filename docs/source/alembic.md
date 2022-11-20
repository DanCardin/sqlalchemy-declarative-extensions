# Alembic

A significant usecase for this libarary includes extending Alembic's autogenerate
system (`alembic revision --autogenerate`) such that it ensures the existence
of the declared objects.

One can opt into registering into alembic's event system using `register_alembic_events`.
This should almost certainly happen inside alembic's `env.py`.

```python
# env.py
from sqlalchemy_declarative_extensions import register_alembic_events

register_alembic_events(schemas=True, roles=True, grants=True, rows=True)
```

Note, all available options are enabled by default. Given that Alembic is the
primary intended usecase for the library, it's most likely that any defined
object types are indended to be used by alembic.
