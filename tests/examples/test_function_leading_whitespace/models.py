from sqlalchemy_declarative_extensions import Function, Functions, declarative_database
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    functions = Functions().are(
        Function(
            "samesame",
            """
            BEGIN
                RETURN NEW;
            END
            """,
            returns="trigger",
            language="plpgsql",
        )
    )
