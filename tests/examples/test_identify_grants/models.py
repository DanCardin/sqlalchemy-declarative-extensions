import sqlalchemy
from sqlalchemy import Column, types
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_declarative_extensions import declarative_database
from sqlalchemy_declarative_extensions.grant import Grants
from sqlalchemy_declarative_extensions.grant.postgresql import for_role
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
        for_role("o2_read").grant("select").default().on_tables_in_schema("public"),
        for_role("o2_write")
        .grant("insert", "update", "delete")
        .default()
        .on_tables_in_schema("public"),
    )


class Foo(Base):
    __tablename__ = "foo"

    id = Column(types.Integer(), autoincrement=True, primary_key=True)
