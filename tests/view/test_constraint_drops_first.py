from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, text, types

from sqlalchemy_declarative_extensions import (
    Schemas,
    Views,
    declarative_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base
from sqlalchemy_declarative_extensions.view.compare import compare_views

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    schemas = Schemas().are("fooschema")
    views = Views()


class Foo(Base):
    __tablename__ = "foo"
    __table_args__ = {"schema": "fooschema"}

    id = Column(types.Integer(), primary_key=True)
    value = Column(types.Integer())


register_sqlalchemy_events(Base.metadata, schemas=True, views=True, rows=True)

pg = create_postgres_fixture(
    scope="function", engine_kwargs={"echo": True}, session=True
)


def test_constraint_changes(pg):
    """Assert the constraint drops **before** the view drop itself."""
    pg.execute(text("CREATE SCHEMA fooschema"))
    pg.execute(text("CREATE TABLE fooschema.foo (id integer, value integer)"))
    pg.execute(
        text(
            "CREATE MATERIALIZED VIEW fooschema.bar AS (SELECT id, value FROM fooschema.foo WHERE id < 10)"
        )
    )
    pg.execute(text('CREATE UNIQUE INDEX "ix_id" ON "fooschema"."bar" (value)'))
    pg.commit()

    views = Base.metadata.info["views"]
    connection = pg.connection()
    result = compare_views(connection, views)
    sql_statements = result[0].to_sql(connection.dialect)
    assert len(sql_statements) == 2

    assert sql_statements[0] == """DROP INDEX "fooschema"."ix_id";"""
    assert sql_statements[1] == "DROP MATERIALIZED VIEW fooschema.bar"

    for statement in sql_statements:
        pg.execute(text(statement))
