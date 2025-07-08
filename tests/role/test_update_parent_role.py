from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import text

from sqlalchemy_declarative_extensions import Roles
from sqlalchemy_declarative_extensions.dialects.postgresql import Role
from sqlalchemy_declarative_extensions.role.compare import compare_roles

roles = Roles(ignore_unspecified=True).are(
    "parent1",
    "parent2",
    Role("child_no_parent"),
    Role("child_with_parent", in_roles=["parent1", "parent2"]),
    Role("child_parent_wrong_order", in_roles=["parent2", "parent1"]),
)


pg = create_postgres_fixture(scope="function", engine_kwargs={"echo": True})


def test_createall_role(pg):
    with pg.connect() as conn:
        with conn.begin() as trans:
            conn.execute(text("CREATE ROLE parent1"))
            conn.execute(text("CREATE ROLE parent2"))

            # Incorrectly has parents
            conn.execute(text("CREATE ROLE child_no_parent IN ROLE parent1, parent2"))

            # Incorrectly has no parents
            conn.execute(text("CREATE ROLE child_with_parent"))

            # Has correct parents in a different order than defined
            conn.execute(
                text("CREATE ROLE child_parent_wrong_order IN ROLE parent1, parent2")
            )

            trans.commit()

        result = compare_roles(conn, roles)
    assert len(result) == 2

    child_no_parent_diff = result[0].to_sql()
    assert child_no_parent_diff == [
        """REVOKE "parent1" FROM "child_no_parent";""",
        """REVOKE "parent2" FROM "child_no_parent";""",
    ]

    child_with_parent_diff = result[1].to_sql()
    assert child_with_parent_diff == [
        """GRANT "parent1" TO "child_with_parent";""",
        """GRANT "parent2" TO "child_with_parent";""",
    ]
