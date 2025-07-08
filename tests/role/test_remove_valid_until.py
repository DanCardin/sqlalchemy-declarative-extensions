from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import text

from sqlalchemy_declarative_extensions import Roles
from sqlalchemy_declarative_extensions.dialects.postgresql import Role
from sqlalchemy_declarative_extensions.role.compare import compare_roles

roles = Roles(ignore_unspecified=True).are(
    Role("forever_valid", valid_until=None),
)

pg = create_postgres_fixture(scope="function", engine_kwargs={"echo": True})


def test_valid_until_date_being_removed(pg):
    with pg.connect() as conn:
        with conn.begin() as trans:
            conn.execute(text("CREATE ROLE forever_valid WITH PASSWORD 'p';"))
            conn.execute(text("ALTER ROLE forever_valid VALID UNTIL '2020-01-01'"))
            trans.commit()

        result = compare_roles(conn, roles)
    assert len(result) == 1
    sql = result[0].to_sql()
    assert sql == ["""ALTER ROLE "forever_valid" WITH VALID UNTIL 'infinity';"""]


def test_valid_until_infinity_ignored(pg):
    with pg.connect() as conn:
        with conn.begin() as trans:
            conn.execute(text("CREATE ROLE forever_valid WITH PASSWORD 'p';"))
            conn.execute(text("ALTER ROLE forever_valid VALID UNTIL 'infinity'"))
            trans.commit()

        result = compare_roles(conn, roles)
    assert len(result) == 0


def test_valid_until_null_ignored(pg):
    with pg.connect() as conn:
        with conn.begin() as trans:
            conn.execute(text("CREATE ROLE forever_valid WITH PASSWORD 'p';"))
            trans.commit()

        result = compare_roles(conn, roles)
    assert len(result) == 0
