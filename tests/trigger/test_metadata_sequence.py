import pytest
import sqlalchemy

from sqlalchemy_declarative_extensions import (
    Trigger,
    Triggers,
    declare_database,
)

metadata1 = sqlalchemy.MetaData()
metadata2 = sqlalchemy.MetaData()
metadata3 = sqlalchemy.MetaData()

declare_database(metadata1, triggers=Triggers().are(Trigger("foo", "", "")))
declare_database(metadata2, triggers=Triggers().are(Trigger("bar", "", "")))
declare_database(metadata3, triggers=Triggers(ignore_unspecified=True))


def test_invalid_combination():
    with pytest.raises(ValueError):
        Triggers.extract([metadata1, metadata3])


def test_valid_combination():
    procedures = Triggers.extract([metadata1, metadata2])
    assert procedures == Triggers(
        triggers=[Trigger("foo", "", ""), Trigger("bar", "", "")]
    )


def test_single():
    triggers = Triggers.extract(metadata1)
    assert triggers is metadata1.info["triggers"]
