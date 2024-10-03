import pytest
import sqlalchemy

from sqlalchemy_declarative_extensions import (
    Row,
    Rows,
    declare_database,
)

metadata1 = sqlalchemy.MetaData()
metadata2 = sqlalchemy.MetaData()
metadata3 = sqlalchemy.MetaData()

declare_database(metadata1, rows=Rows().are(Row("foo")))
declare_database(metadata2, rows=Rows().are(Row("bar")))


def test_invalid_combination():
    with pytest.raises(NotImplementedError):
        Rows.extract([metadata1, metadata1])


def test_single():
    rows = Rows.extract(metadata1)
    assert rows
    assert rows[0] is metadata1.info["rows"]
    assert rows[1] is metadata1

    rows = Rows.extract([metadata1, metadata3])
    assert rows
    assert rows[0] is metadata1.info["rows"]
    assert rows[1] is metadata1
