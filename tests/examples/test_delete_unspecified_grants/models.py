from sqlalchemy import Column, types
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_declarative_extensions import declarative_database
from sqlalchemy_declarative_extensions.grant import Grants
from sqlalchemy_declarative_extensions.grant.postgresql import PGGrant
from sqlalchemy_declarative_extensions.role import PGRole, Roles

_Base = declarative_base()


@declarative_database
class Base(_Base):
    __abstract__ = True

    roles = Roles(ignore_unspecified=True).are(
        "o2_read",
        "o2_write",
        PGRole("o1_app", login=False, in_roles=["o2_read", "o2_write"]),
    )
    grants = Grants().are(
        PGGrant("o2_read").grant("select").default().on_tables_in_schema("public"),
    )


class Foo(Base):
    __tablename__ = "foo"

    id = Column(types.Integer(), primary_key=True)
