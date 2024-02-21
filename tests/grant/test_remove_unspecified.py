import pytest
import sqlalchemy.exc
from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, text, types

from sqlalchemy_declarative_extensions import (
    Grants,
    Roles,
    declarative_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.grant.compare import compare_grants
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    roles = Roles(ignore_unspecified=True).are("read")
    grants = Grants()


class Foo(Base):
    __tablename__ = "foo"

    id = Column(types.Integer(), autoincrement=True, primary_key=True)


pg = create_postgres_fixture(scope="function", engine_kwargs={"echo": True})
register_sqlalchemy_events(Base.metadata, schemas=True, roles=True, grants=True)


@pytest.mark.grant
def test_createall_grant(pg):
    with pg.connect() as conn:
        with conn.begin() as trans:
            conn.execute(text("create role read"))
            conn.execute(
                text(
                    "alter default privileges in schema public grant insert, update, delete on tables to read"
                )
            )
            conn.execute(
                text(
                    "alter default privileges in schema public grant usage on sequences to read"
                )
            )
            conn.execute(text("create table meow (id serial)"))
            conn.execute(text('GRANT INSERT ON TABLE meow to "read"'))
            conn.execute(text('GRANT USAGE ON SEQUENCE meow_id_seq to "read"'))
            trans.commit()

    Base.metadata.create_all(bind=pg)

    # There should be no diffs detected after running `create_all`
    grants = Base.metadata.info["grants"]
    roles = Base.metadata.info["roles"]
    with pg.connect() as conn:
        diff = compare_grants(conn, grants, roles)
    assert len(diff) == 0

    # Assert nothing can do anything!
    with pytest.raises(sqlalchemy.exc.ProgrammingError):
        with pg.connect() as conn:
            conn.execute(text("SET ROLE read; SELECT * FROM foo"))

    with pytest.raises(sqlalchemy.exc.ProgrammingError):
        with pg.connect() as conn:
            conn.execute(text("SET ROLE read; INSERT INTO foo VALUES (DEFAULT)"))

    with pytest.raises(sqlalchemy.exc.ProgrammingError):
        with pg.connect() as conn:
            conn.execute(text("SET ROLE read; INSERT INTO meow VALUES (DEFAULT)"))
