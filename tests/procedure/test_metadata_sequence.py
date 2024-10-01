import pytest
import sqlalchemy

from sqlalchemy_declarative_extensions import (
    Procedure,
    Procedures,
    declare_database,
)

metadata1 = sqlalchemy.MetaData()
metadata2 = sqlalchemy.MetaData()
metadata3 = sqlalchemy.MetaData()

declare_database(
    metadata1, procedures=Procedures(ignore=["one"]).are(Procedure("foo", ""))
)
declare_database(
    metadata2, procedures=Procedures(ignore=["two"]).are(Procedure("bar", ""))
)
declare_database(metadata3, procedures=Procedures(ignore_unspecified=True))


def test_invalid_combination():
    with pytest.raises(ValueError):
        Procedures.extract([metadata1, metadata3])


def test_valid_combination():
    procedures = Procedures.extract([metadata1, metadata2])
    assert procedures == Procedures(
        procedures=[Procedure("foo", ""), Procedure("bar", "")], ignore=["one", "two"]
    )


def test_single():
    procedures = Procedures.extract(metadata1)
    assert procedures is metadata1.info["procedures"]
