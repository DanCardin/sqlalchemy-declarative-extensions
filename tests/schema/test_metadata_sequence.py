import pytest
import sqlalchemy

from sqlalchemy_declarative_extensions import (
    Schema,
    Schemas,
    declare_database,
)

metadata1 = sqlalchemy.MetaData()
metadata2 = sqlalchemy.MetaData()
metadata3 = sqlalchemy.MetaData()

declare_database(metadata1, schemas=Schemas().are("foo"))
declare_database(metadata2, schemas=Schemas().are("bar"))
declare_database(metadata3, schemas=Schemas(ignore_unspecified=True).are("baz"))


def test_invalid_combination():
    with pytest.raises(ValueError):
        Schemas.extract([metadata1, metadata3])


def test_valid_combination():
    schemas = Schemas.extract([metadata1, metadata2])
    assert schemas == Schemas(schemas=(Schema("foo"), Schema("bar")))


def test_single():
    schemas = Schemas.extract(metadata1)
    assert schemas is metadata1.info["schemas"]
