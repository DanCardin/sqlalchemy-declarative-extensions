from types import ModuleType
from typing import Optional

try:
    import alembic as alembic_

    alembic: Optional[ModuleType] = alembic_
except ImportError:
    alembic = None


__all__ = [
    "alembic",
]
