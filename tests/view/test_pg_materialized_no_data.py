import pytest
import sqlalchemy.exc
from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, text, types

from sqlalchemy_declarative_extensions import (
    Row,
    Rows,
    declarative_database,
    register_sqlalchemy_events,
    view,
)
from sqlalchemy_declarative_extensions.dialects.postgresql import MaterializedOptions
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base
from tests import skip_sqlalchemy13

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    rows = Rows().are(
        Row("foo", id=1), Row("foo", id=2), Row("foo", id=12), Row("foo", id=13)
    )


class Foo(Base):
    __tablename__ = "foo"

    id = Column(types.Integer(), primary_key=True)


@view(
    Base,
    materialized=MaterializedOptions(with_data=True),
    register_as_model=True,
)
class Eager:
    __tablename__ = "eager"
    __view__ = "select id from foo where id < 10"

    id = Column(types.Integer(), primary_key=True)


@view(
    Base,
    materialized=MaterializedOptions(with_data=False),
    register_as_model=True,
)
class Lazy:
    __tablename__ = "lazy"
    __view__ = "select id from foo where id < 10"

    id = Column(types.Integer(), primary_key=True)


@view(Base, materialized={"with_data": False}, register_as_model=True)
class Lazy2:
    __tablename__ = "lazy2"
    __view__ = "select id from foo where id < 10"

    id = Column(types.Integer(), primary_key=True)


register_sqlalchemy_events(Base.metadata, schemas=True, views=True, rows=True)

pg = create_postgres_fixture(
    scope="function", engine_kwargs={"echo": True}, session=True
)


@skip_sqlalchemy13
def test_create_view_postgresql_eager(pg):
    Base.metadata.create_all(bind=pg.connection())
    pg.commit()

    result = [f.id for f in pg.query(Foo).all()]
    assert result == [1, 2, 12, 13]

    result = [f.id for f in pg.query(Eager).all()]
    assert result == []

    pg.execute(text("refresh materialized view eager"))
    result = [f.id for f in pg.query(Eager).all()]
    assert result == [1, 2]


@skip_sqlalchemy13
def test_create_view_postgresql_lazy(pg):
    Base.metadata.create_all(bind=pg.connection())
    pg.commit()

    with pytest.raises(sqlalchemy.exc.OperationalError) as e:
        pg.query(Lazy).all()
    assert 'materialized view "lazy" has not been populated' in str(e)

    pg.rollback()
    pg.execute(text("refresh materialized view lazy"))
    result = [f.id for f in pg.query(Lazy).all()]
    assert result == [1, 2]


@skip_sqlalchemy13
def test_create_view_postgresql_lazy2(pg):
    Base.metadata.create_all(bind=pg.connection())
    pg.commit()

    with pytest.raises(sqlalchemy.exc.OperationalError) as e:
        pg.query(Lazy2).all()
    assert 'materialized view "lazy2" has not been populated' in str(e)

    pg.rollback()
    pg.execute(text("refresh materialized view lazy2"))
    result = [f.id for f in pg.query(Lazy2).all()]
    assert result == [1, 2]
