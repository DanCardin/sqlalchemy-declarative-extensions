import pytest
from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import Column, text, types
from sqlalchemy.exc import ProgrammingError

from sqlalchemy_declarative_extensions import (
    declarative_database,
    register_procedure,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.dialects.postgresql import Procedure
from sqlalchemy_declarative_extensions.dialects.postgresql.grant import (
    DefaultGrant,
)
from sqlalchemy_declarative_extensions.dialects.postgresql.role import Role
from sqlalchemy_declarative_extensions.grant.base import Grants
from sqlalchemy_declarative_extensions.procedure.compare import compare_procedures
from sqlalchemy_declarative_extensions.role.base import Roles
from sqlalchemy_declarative_extensions.sqlalchemy import declarative_base

_Base = declarative_base()


@declarative_database
class Base(_Base):  # type: ignore
    __abstract__ = True

    roles = Roles(ignore_unspecified=True).are(Role("can_insert"), Role("cant_insert"))
    grants = Grants().are(
        DefaultGrant.on_tables_in_schema("public").grant("select", to="cant_insert"),
        DefaultGrant.on_tables_in_schema("public")
        .grant("insert", to="cant_insert")
        .invert(),
        DefaultGrant.on_tables_in_schema("public").grant(
            "insert", "select", to="can_insert"
        ),
    )


class Foo(Base):
    __tablename__ = "foo"

    id = Column(types.Integer(), primary_key=True)


procedure_invoker = Procedure(
    "add_one_invoker",
    """
    DECLARE
        m INTEGER;
    BEGIN
    SELECT coalesce(max(id), 0) + 1 INTO m FROM foo;
    INSERT INTO foo (id) VALUES (m);
    END
    """,
).with_language("plpgsql")

procedure_definer = procedure_invoker.with_security_definer().with_name(
    "add_one_definer"
)

register_procedure(Base.metadata, procedure_invoker)
register_procedure(Base.metadata, procedure_definer)


register_sqlalchemy_events(Base.metadata, roles=True, grants=True, procedures=True)

pg = create_postgres_fixture(engine_kwargs={"echo": True}, session=True)


def test_procedure_security(pg):
    Base.metadata.create_all(bind=pg.connection())
    pg.commit()

    # Permission decided by invoker
    pg.execute(text("SET ROLE cant_insert"))
    with pytest.raises(ProgrammingError) as e:
        result = pg.execute(text("CALL add_one_invoker()")).scalar()
    assert "permission denied for table foo" in str(e)

    pg.rollback()

    pg.execute(text("SET ROLE can_insert"))
    pg.execute(text("CALL add_one_invoker()"))
    result = pg.execute(text("SELECT max(id) from foo")).scalar()
    assert result == 1

    # Permission decided by definer
    pg.execute(text("SET ROLE cant_insert"))
    pg.execute(text("CALL add_one_definer()"))
    result = pg.execute(text("SELECT max(id) from foo")).scalar()
    assert result == 2

    pg.execute(text("SET ROLE can_insert"))
    pg.execute(text("CALL add_one_definer()"))
    result = pg.execute(text("SELECT max(id) from foo")).scalar()
    assert result == 3

    # Just a double check
    result = pg.query(Foo.id).count()
    assert result == 3

    connection = pg.connection()
    diff = compare_procedures(connection, Base.metadata.info["procedures"])
    assert diff == []
