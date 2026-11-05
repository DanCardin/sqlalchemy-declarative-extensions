import pytest
from sqlalchemy import MetaData

from sqlalchemy_declarative_extensions.dialects.postgresql import (
    Trigger,
    trigger_function,
)
from sqlalchemy_declarative_extensions.trigger.base import register_trigger


def test_different_functions_with_the_same_name_raise():
    metadata = MetaData()
    register_trigger(
        metadata,
        Trigger.after(
            "insert",
            on="a",
            name="a",
            execute=trigger_function("audit", "BEGIN RETURN NULL; END"),
        ),
    )

    with pytest.raises(ValueError, match="'audit'"):
        register_trigger(
            metadata,
            Trigger.after(
                "insert",
                on="b",
                name="b",
                execute=trigger_function("audit", "BEGIN RETURN NEW; END"),
            ),
        )

    assert [t.name for t in metadata.info["triggers"]] == ["a"]
