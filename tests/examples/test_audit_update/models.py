from sqlalchemy import Boolean, Column, Integer, String, Table

from sqlalchemy_declarative_extensions.audit import audit_table
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


class Base(_Base):
    __abstract__ = True

    schemas = ["audit"]


user_table = Table(
    "user_account",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(30)),
    Column("added", Boolean()),
)

user_audit_table = audit_table(user_table, schema="audit")
