from sqlalchemy import Column, types
from sqlalchemy.orm import declarative_base

from sqlalchemy_declarative_extensions import Functions, declarative_database
from sqlalchemy_declarative_extensions.dialects.postgresql import Function, FunctionVolatility

_Base = declarative_base()


@declarative_database
class Base(_Base): # type: ignore
    __abstract__ = True

    functions = Functions().are(
        Function(
            "add_stable",
            "SELECT i + 1;",
            parameters=["i integer"],
            returns="INTEGER",
            volatility=FunctionVolatility.STABLE,
        ),
        # NEW FUNCTION: Multiple params, RETURNS TABLE, plpgsql
        Function(
            "get_users_by_group",
            """
            BEGIN
                -- Dummy implementation for testing definition
                RETURN QUERY SELECT dt.id, dt.id::text as name FROM dummy_table dt WHERE dt.id = any(group_ids);
            END;
            """,
            parameters=["group_ids integer[]"],
            returns="TABLE(id integer, name text)",
            language="plpgsql", # Requires plpgsql
            volatility=FunctionVolatility.STABLE,
        ),
    )


# Include a dummy table just in case it's needed
class DummyTable(Base):
    __tablename__ = "dummy_table"
    id = Column(types.Integer, primary_key=True)