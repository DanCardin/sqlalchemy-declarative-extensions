import sqlalchemy
from sqlalchemy import Column, types

from sqlalchemy_declarative_extensions import Roles, declarative_database
from sqlalchemy_declarative_extensions.dialects.postgresql import Role
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    roles = Roles(ignore_roles=["user"]).are(
        "read",
        Role(
            "admin",
            login=True,
            superuser=False,
            createdb=True,
            inherit=True,
            createrole=True,
            replication=True,
            bypass_rls=True,
            in_roles=["read"],
        ),
    )


class CreatedAt(Base):
    __tablename__ = "foo"

    id = Column(types.Integer(), autoincrement=True, primary_key=True)

    created_at = sqlalchemy.Column(
        sqlalchemy.types.DateTime(timezone=True),
        server_default=sqlalchemy.text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
