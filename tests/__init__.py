import pytest
import sqlalchemy

sqlalchemy_version = getattr(sqlalchemy, "__version__", "1.3")


skip_sqlalchemy13 = pytest.mark.skipif(
    sqlalchemy_version.startswith("1.3"),
    reason="Incompatible with sqlalchemy 1.3 behavior",
)
