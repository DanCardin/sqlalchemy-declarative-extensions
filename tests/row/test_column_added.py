from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, text, types

from sqlalchemy_declarative_extensions import (
    Row,
    Rows,
    declarative_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.row.compare import (
    compare_rows,
)
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    rows = Rows(ignore_unspecified=True).are(
        Row("foo", id=1),
    )


class Foo(Base):
    __tablename__ = "foo"

    id = Column(types.Integer(), primary_key=True)
    name = Column(types.Unicode(), nullable=True)


register_sqlalchemy_events(Base.metadata, rows=True)

pg = create_postgres_fixture(
    scope="function", engine_kwargs={"echo": True}, session=True
)


def test_column_added(pg):
    pg.execute(text("CREATE TABLE foo (id SERIAL PRIMARY KEY)"))
    pg.commit()

    Base.metadata.create_all(bind=pg.connection())
    pg.commit()

    result = pg.execute(text("SELECT * FROM foo")).fetchall()
    assert result == [(1,)]

    pg.execute(text("ALTER TABLE foo ADD name VARCHAR"))
    pg.commit()

    rows = Rows(ignore_unspecified=True).are(
        Row("foo", id=1, name="qwer"),
    )
    result = compare_rows(pg.connection(), Base.metadata, rows)
    for op in result:
        for query in op.render(Base.metadata):
            pg.execute(query)
    pg.commit()

    result = pg.execute(text("SELECT * FROM foo")).fetchall()
    assert result == [(1, "qwer")]
