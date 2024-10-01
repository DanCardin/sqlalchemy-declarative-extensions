import pytest
import sqlalchemy

from sqlalchemy_declarative_extensions import (
    Function,
    Functions,
    declare_database,
)

metadata1 = sqlalchemy.MetaData()
metadata2 = sqlalchemy.MetaData()
metadata3 = sqlalchemy.MetaData()

declare_database(
    metadata1, functions=Functions(ignore=["one"]).are(Function("foo", ""))
)
declare_database(
    metadata2, functions=Functions(ignore=["two"]).are(Function("bar", ""))
)
declare_database(metadata3, functions=Functions(ignore_unspecified=True))


def test_invalid_combination():
    with pytest.raises(ValueError):
        Functions.extract([metadata1, metadata3])


def test_valid_combination():
    functions = Functions.extract([metadata1, metadata2])
    assert functions == Functions(
        functions=[Function("foo", ""), Function("bar", "")], ignore=["one", "two"]
    )


def test_single():
    functions = Functions.extract(metadata1)
    assert functions is metadata1.info["functions"]
