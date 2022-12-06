from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_declarative_extensions import Roles, Schemas, declarative_database
from sqlalchemy_declarative_extensions.dialects.postgresql import DefaultGrant

_Base = declarative_base()


@declarative_database
class Base(_Base):
    __abstract__ = True

    schemas = Schemas().are("foo")
    roles = Roles(ignore_unspecified=True).are("bar")
    grants = [
        DefaultGrant.on_tables_in_schema("foo").grant("select", to="bar"),
    ]
