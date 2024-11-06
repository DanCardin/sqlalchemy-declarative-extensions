import pytest
import sqlalchemy
from sqlalchemy.sql.schema import DEFAULT_NAMING_CONVENTION

from sqlalchemy_declarative_extensions import (
    View,
    Views,
    declare_database,
)

metadata1 = sqlalchemy.MetaData()
metadata2 = sqlalchemy.MetaData()
metadata3 = sqlalchemy.MetaData()
metadata4 = sqlalchemy.MetaData()
metadata5 = sqlalchemy.MetaData(naming_convention={"ix": "asdf"})

declare_database(metadata1, views=Views(ignore=["one"]).are(View("foo", "")))
declare_database(metadata2, views=Views(ignore_views=["two"]).are(View("bar", "")))
declare_database(metadata3, views=Views(ignore_unspecified=True).are(View("baz", "")))
declare_database(
    metadata4,
    views=Views(naming_convention={"ix": "asdf"}).are(View("baz", "")),
)
declare_database(metadata5, views=Views().are(View("bax", "")))


def test_invalid_combination():
    with pytest.raises(ValueError):
        Views.extract([metadata1, metadata3])

    with pytest.raises(ValueError):
        Views.extract([metadata1, metadata4])

    with pytest.raises(ValueError):
        Views.extract([metadata1, metadata5])


def test_valid_combination():
    views = Views.extract([metadata1, metadata2])
    assert views == Views(
        views=[View("foo", ""), View("bar", "")],
        ignore=["one"],
        ignore_views=["two"],
        naming_convention=DEFAULT_NAMING_CONVENTION,
    )


def test_single():
    views = Views.extract(metadata5)
    assert views
    assert views.naming_convention == {"ix": "asdf"}


def test_naming_convention_fallback():
    metadatat1 = sqlalchemy.MetaData(naming_convention={"ix": "asdf"})
    metadatat2 = sqlalchemy.MetaData(naming_convention={"ix": "asdf"})
    declare_database(metadatat1, views=Views())
    declare_database(metadatat2, views=Views())

    views = Views.extract([metadatat1, metadatat2])
    assert views
    assert views.naming_convention == {"ix": "asdf"}
