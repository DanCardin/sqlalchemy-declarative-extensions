from sqlalchemy import Column, Integer

from sqlalchemy_declarative_extensions import Row, Rows, declarative_database
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    rows = Rows().are(
        Row("tab", id=1, value=1),
        Row("tab", id=2, value=3),
    )


class Tab(Base):
    __tablename__ = "tab"

    id = Column(Integer, primary_key=True)
    value = Column(Integer)
