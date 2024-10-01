from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, text, types

from sqlalchemy_declarative_extensions import (
    Procedure,
    declarative_database,
    register_procedure,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.procedure.compare import compare_procedures
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True


procedure = Procedure(
    "gimme",
    """


                INSERT INTO foo (id) VALUES (DEFAULT);
    """,
)
register_procedure(Base.metadata, procedure)


class Foo(Base):
    __tablename__ = "foo"

    id = Column(types.Integer(), primary_key=True)


register_sqlalchemy_events(Base.metadata, procedures=True)

pg = create_postgres_fixture(engine_kwargs={"echo": True}, session=True)


def test_create_with_complex_procedure_requiring_normalization(pg):
    Base.metadata.create_all(bind=pg.connection())
    pg.commit()

    pg.execute(text("CALL gimme()"))

    result = pg.query(Foo.id).scalar()
    assert result == 1

    connection = pg.connection()
    diff = compare_procedures(connection, Base.metadata.info["procedures"])
    assert diff == []
