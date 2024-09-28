import pytest
import sqlalchemy

from sqlalchemy_declarative_extensions import (
    Grants,
    declare_database,
)
from sqlalchemy_declarative_extensions.dialects.postgresql import Grant

metadata1 = sqlalchemy.MetaData()
metadata2 = sqlalchemy.MetaData()
metadata3 = sqlalchemy.MetaData()
metadata4 = sqlalchemy.MetaData()
metadata5 = sqlalchemy.MetaData()
metadata6 = sqlalchemy.MetaData()

declare_database(
    metadata1, grants=Grants().are(Grant.new("select", to="foo").on_tables())
)
declare_database(
    metadata2, grants=Grants().are(Grant.new("select", to="bar").on_tables())
)
declare_database(
    metadata3,
    grants=Grants(ignore_unspecified=True).are(
        Grant.new("select", to="baz").on_tables()
    ),
)
declare_database(
    metadata4,
    grants=Grants(ignore_self_grants=False).are(
        Grant.new("select", to="baz").on_tables()
    ),
)
declare_database(
    metadata5,
    grants=Grants(only_defined_roles=False).are(
        Grant.new("select", to="baz").on_tables()
    ),
)
declare_database(
    metadata6,
    grants=Grants(default_grants_imply_grants=False).are(
        Grant.new("select", to="baz").on_tables()
    ),
)


def test_invalid_combination():
    with pytest.raises(ValueError):
        Grants.extract([metadata1, metadata3])

    with pytest.raises(ValueError):
        Grants.extract([metadata1, metadata4])

    with pytest.raises(ValueError):
        Grants.extract([metadata1, metadata5])

    with pytest.raises(ValueError):
        Grants.extract([metadata1, metadata6])


def test_valid_combination():
    schemas = Grants.extract([metadata1, metadata2])
    assert schemas == Grants(
        grants=[
            Grant.new("select", to="foo").on_tables(),
            Grant.new("select", to="bar").on_tables(),
        ]
    )


def test_single():
    grants = Grants.extract(metadata1)
    assert grants is metadata1.info["grants"]
