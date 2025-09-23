from sqlalchemy import text
from sqlalchemy.engine import Engine, create_engine

from sqlalchemy_declarative_extensions import (
    declarative_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    schemas = ["foo"]


register_sqlalchemy_events(Base.metadata, schemas=True, views=True)


def test_create_schemas_filtered_to_database(snowflake: Engine):
    """Ensure the `get_schemas` call is scoped to the current database.

    This may only be a behavior specific to `fakesnow`, but without a catalog filter,
    two databases with the same schemas will appear exist. In real snowflake, when
    scoped to a database, you only get the current database anyways; but it should have
    no effect otherwise.
    """
    Base.metadata.create_all(bind=snowflake)

    engine = create_engine("snowflake://user:password@account/db/schema")
    with engine.connect() as conn:
        Base.metadata.create_all(engine)

        schemas = conn.execute(
            text(
                "SELECT schema_name"
                " FROM information_schema.schemata"
                " WHERE catalog_name = current_database()"
                " AND schema_name ilike 'foo'"
            )
        ).all()
    assert schemas == [("FOO",)]
