from pytest_mock_resources import create_postgres_fixture
from sqlalchemy.orm import Mapped, mapped_column

from sqlalchemy_declarative_extensions import (
    declarative_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.audit import audit
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore  # type: ignore
    __abstract__ = True


@audit()
class Something(Base):
    __tablename__ = "Something"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    end: Mapped[int] = mapped_column()


register_sqlalchemy_events(Base.metadata, functions=True, triggers=True)

pg = create_postgres_fixture(engine_kwargs={"echo": True}, session=True)


def test_quoted_name(pg):
    Base.metadata.create_all(bind=pg.connection())
    pg.commit()

    pg.add(Something(end=2))
    pg.commit()
