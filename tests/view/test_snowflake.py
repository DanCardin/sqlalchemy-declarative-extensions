from sqlalchemy import Column, text, types
from sqlalchemy.engine import Engine

from sqlalchemy_declarative_extensions import (
    declarative_database,
    register_sqlalchemy_events,
    view,
)
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    schemas = ["foo"]


@view(Base, register_as_model=True)
class Bar:
    __tablename__ = "bar"
    __table_args__ = {"schema": "foo"}
    __view__ = (
        "select table_catalog, table_schema, table_name from information_schema.views"
    )

    id = Column(types.Integer(), primary_key=True)


register_sqlalchemy_events(Base.metadata, schemas=True, views=True)


def test_create_view_snowflake(snowflake: Engine):
    Base.metadata.create_all(bind=snowflake)

    with snowflake.connect() as conn:
        result = conn.execute(text("select * from foo.bar")).all()
    assert result == [("TEST", "FOO", "BAR")]


def test_update_view_snowflake(snowflake: Engine):
    with snowflake.connect() as conn:
        conn.execute(text("CREATE SCHEMA foo"))
        conn.execute(
            text(
                "CREATE VIEW foo.bar AS SELECT table_schema FROM information_schema.views"
            )
        )

    with snowflake.connect() as conn:
        result = conn.execute(text("select * from foo.bar")).all()
    assert result == [("FOO",)]

    Base.metadata.create_all(bind=snowflake)

    with snowflake.connect() as conn:
        result = conn.execute(text("select * from foo.bar")).all()
    assert result == [("TEST", "FOO", "BAR")]
