from sqlalchemy_declarative_extensions import Procedure, declarative_database
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    procedures = [Procedure("gimme", "SELECT 1;")]
