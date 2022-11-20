from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, text, types
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_declarative_extensions import (
    declarative_database,
    register_sqlalchemy_events,
    Row,
    Rows,
)
from sqlalchemy_declarative_extensions.row.compare import (
    compare_rows,
    DeleteRowOp,
    UpdateRowOp,
)

Base_ = declarative_base()


@declarative_database
class Base(Base_):
    __abstract__ = True

    rows = Rows(ignore_unspecified=True).are(
        Row("foo.foo", id=2, name="asdf"),
        Row("foo.foo", id=3, name="qwer", active=False),
    )


class Foo(Base):
    __tablename__ = "foo"
    __table_args__ = {"schema": "foo"}

    id = Column(types.Integer(), primary_key=True)
    name = Column(types.Unicode(), nullable=False)
    active = Column(types.Boolean())


register_sqlalchemy_events(Base.metadata, rows=True)

pg = create_postgres_fixture(
    scope="function", engine_kwargs={"echo": True}, session=True
)


def test_insert_missing(pg):
    pg.execute(text("CREATE SCHEMA foo"))
    pg.commit()
    Base.metadata.create_all(bind=pg.connection())

    foos = pg.query(Foo).all()
    assert len(foos) == 2
    assert foos[0].id == 2
    assert foos[0].name == "asdf"
    assert foos[0].active is None

    assert foos[1].id == 3
    assert foos[1].name == "qwer"
    assert foos[1].active is False


def test_only_diff_supplied_values(pg):
    """Assert that only the supplied values are compared and unspecified values are ignored."""
    pg.execute(text("CREATE SCHEMA foo"))
    pg.commit()

    connection = pg.connection()
    Base.metadata.create_all(bind=connection)

    rows = Rows().are(
        Row("foo.foo", id=2, name="asdf"),
        Row("foo.foo", id=3, active=False),
    )
    result = compare_rows(connection, Base.metadata, rows)

    assert result == []

    rows = Rows().are(
        Row("foo.foo", id=2, name="asdf"),
        Row("foo.foo", id=3, active=True),
    )
    result = compare_rows(connection, Base.metadata, rows)
    assert isinstance(result[0], UpdateRowOp)
    assert result[0].to_values["active"] is True


def test_delete_unspecified_rows(pg):
    """Assert that rows missing from the input set are indicated to be deleted."""
    pg.execute(text("CREATE SCHEMA foo"))
    pg.commit()

    connection = pg.connection()
    Base.metadata.create_all(bind=connection)

    rows = Rows().are(
        Row("foo.foo", id=3, name="qwer", active=False),
    )
    result = compare_rows(connection, Base.metadata, rows)

    assert isinstance(result[0], DeleteRowOp)
    assert result[0].values["id"] == 2
