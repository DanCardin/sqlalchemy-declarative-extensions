import pytest

from sqlalchemy_declarative_extensions.dialects import mysql
from sqlalchemy_declarative_extensions.dialects.postgresql import trigger_function


def test_function_is_rejected():
    audit = trigger_function("audit", "BEGIN RETURN NULL; END")

    with pytest.raises(TypeError, match="Function"):
        mysql.Trigger.after("insert", execute=audit, on="a", name="a")  # type: ignore
