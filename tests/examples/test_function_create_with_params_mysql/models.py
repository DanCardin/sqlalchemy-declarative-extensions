from sqlalchemy import Column, types
from sqlalchemy.orm import declarative_base

from sqlalchemy_declarative_extensions import Functions, declarative_database
from sqlalchemy_declarative_extensions.dialects.mysql import (
    Function,
    FunctionDataAccess,
    FunctionSecurity,
)

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    functions = Functions().are(
        Function(
            "add_deterministic",
            "RETURN i + 1;",
            parameters=["i integer"],
            returns="INTEGER",
            deterministic=True,
            data_access=FunctionDataAccess.no_sql,
        ),
        # NEW FUNCTION: Multiple params
        Function(
            "add_two_numbers",
            "RETURN a + b;",
            parameters=["a integer", "b integer"],
            returns="INTEGER",
            deterministic=True,
            data_access=FunctionDataAccess.no_sql,
        ),
        # Complex function for Alembic test
        Function(
            "complex_processor",
            "RETURN CONCAT(label, ': ', CAST(val AS CHAR));",
            parameters=["val INT", "label VARCHAR(50)"],
            returns="VARCHAR(100)",
            deterministic=True,
            data_access=FunctionDataAccess.no_sql,
            security=FunctionSecurity.invoker,
        ),
    )


# Include a dummy table just in case it's needed
class DummyTable(Base):
    __tablename__ = "dummy_table"
    id = Column(types.Integer, primary_key=True)
