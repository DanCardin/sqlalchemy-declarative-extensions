from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, text, types

from sqlalchemy_declarative_extensions import (
    Schemas,
    View,
    ViewIndex,
    declarative_database,
    register_sqlalchemy_events,
    register_view,
)
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base
from sqlalchemy_declarative_extensions.view.compare import compare_views

Base_ = declarative_base()


@declarative_database
class Base(Base_):
    __abstract__ = True

    schemas = Schemas().are("fooschema")


class Foo(Base):
    __tablename__ = "foo"
    __table_args__ = {"schema": "fooschema"}

    id = Column(types.Integer(), primary_key=True)


view = View(
    "bar",
    "select id from fooschema.foo where id < 10",
    schema="fooschema",
    materialized=True,
    constraints=[ViewIndex(["id"], unique=True)],
)
register_view(Base.metadata, view)


register_sqlalchemy_events(Base.metadata, schemas=True, views=True, rows=True)

pg = create_postgres_fixture(
    scope="function", engine_kwargs={"echo": True}, session=True
)


def test_constraint_changes(pg):
    """Assert the view itself is not dropped/replaced if only constraints change.

    Constraint drop/create **should** be emitted though! Before this test we had two issues:
        - The view was not considered changed if only constraints changed
        - Fixing the issue to consider constraint changes caused the view itself to be dropped/replaced
    """
    pg.execute(text("CREATE SCHEMA fooschema"))
    pg.execute(text("CREATE TABLE fooschema.foo (id integer)"))

    pg.execute(
        text(
            "CREATE MATERIALIZED VIEW fooschema.bar AS (SELECT id FROM fooschema.foo WHERE id < 10)"
        )
    )
    pg.commit()

    views = Base.metadata.info["views"]
    connection = pg.connection()
    result = compare_views(connection, views, Base.metadata)
    assert len(result) == 1

    sql_statements = result[0].to_sql(connection.dialect)

    assert sql_statements == [
        """CREATE UNIQUE INDEX "ix_id" ON "fooschema"."bar" (id);"""
    ]

    pg.execute(text(sql_statements[0]))
