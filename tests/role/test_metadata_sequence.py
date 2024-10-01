import pytest
import sqlalchemy

from sqlalchemy_declarative_extensions import (
    Role,
    Roles,
    declare_database,
)

metadata1 = sqlalchemy.MetaData()
metadata2 = sqlalchemy.MetaData()
metadata3 = sqlalchemy.MetaData()

declare_database(metadata1, roles=Roles(ignore_roles=["one"]).are("foo"))
declare_database(metadata2, roles=Roles(ignore_roles=["two"]).are("bar"))
declare_database(metadata3, roles=Roles(ignore_unspecified=True).are("baz"))


def test_invalid_combination():
    with pytest.raises(ValueError):
        Roles.extract([metadata1, metadata3])


def test_valid_combination():
    schemas = Roles.extract([metadata1, metadata2])
    assert schemas == Roles(
        roles=(Role("foo"), Role("bar")), ignore_roles=["one", "two"]
    )


def test_single():
    roles = Roles.extract(metadata1)
    assert roles is metadata1.info["roles"]
