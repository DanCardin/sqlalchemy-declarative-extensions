from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, text, types
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_declarative_extensions import declarative_database, Model, Models

Base_ = declarative_base()


@declarative_database
class Base(Base_):
    __abstract__ = True

    models = Models(ignore_unspecified=True).are(
        Model("foo.foo", id=2, name="asdf"),
        Model("foo.foo", id=3, name="qwer", active=False),
    )


class Foo(Base):
    __tablename__ = "foo"
    __table_args__ = {"schema": "foo"}

    id = Column(types.Integer(), primary_key=True)
    name = Column(types.Unicode(), nullable=False)
    active = Column(types.Boolean())


pg = create_postgres_fixture(session=True)


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
