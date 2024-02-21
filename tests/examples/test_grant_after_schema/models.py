from sqlalchemy_declarative_extensions import Roles, Schemas, declarative_database
from sqlalchemy_declarative_extensions.dialects.postgresql import DefaultGrant
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    schemas = Schemas().are("foo")
    roles = Roles(ignore_unspecified=True).are("bar")
    grants = [
        DefaultGrant.on_tables_in_schema("foo").grant("select", to="bar"),
    ]
