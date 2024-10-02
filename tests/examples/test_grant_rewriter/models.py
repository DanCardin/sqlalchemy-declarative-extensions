from sqlalchemy import Column, types

from sqlalchemy_declarative_extensions import Roles, declarative_database
from sqlalchemy_declarative_extensions.dialects.postgresql import DefaultGrant, Role
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    roles = Roles(ignore_unspecified=True).are(
        "o2_read",
        "o2_write",
        Role("o1_app", login=False, in_roles=["o2_read", "o2_write"]),
    )
    grants = [
        DefaultGrant.on_tables_in_schema("public").grant("select", to="o2_read"),
        DefaultGrant.on_tables_in_schema("public").grant(
            "insert", "update", "delete", to="o2_write"
        ),
        DefaultGrant.on_sequences_in_schema("public").grant("usage", to="o2_write"),
    ]


class Foo(Base):
    __tablename__ = "foo"

    id = Column(types.Integer(), primary_key=True)
