import pytest
from sqlalchemy import MetaData, text

from sqlalchemy_declarative_extensions import Roles
from sqlalchemy_declarative_extensions.api import (
    declare_database,
    register_sqlalchemy_events,
)
from sqlalchemy_declarative_extensions.dialects.snowflake import Role
from sqlalchemy_declarative_extensions.role.compare import CreateRoleOp, compare_roles


@pytest.mark.skip
def test_create_roles(snowflake):
    metadata = MetaData()

    roles = Roles(ignore_unspecified=True).are(
        "im_a_role",
        Role(
            "im_a_user",
            login_name="use_me",
            in_roles=["im_a_role"],
        ),
    )

    declare_database(metadata, roles=roles)
    register_sqlalchemy_events(metadata, roles=True)

    with snowflake.connect() as conn:
        ops = compare_roles(conn, roles)

    assert ops == [
        CreateRoleOp(role=Role(name="im_a_role")),
        CreateRoleOp(
            role=Role("im_a_user", in_roles=["im_a_role"], login_name="use_me")
        ),
    ]

    metadata.create_all(bind=snowflake)

    with snowflake.connect() as conn:
        roles = conn.execute(text("SHOW USERS")).fetchall()
    assert len(roles) == 2
    assert roles[0].name == "im_a_role"
    assert roles[1].name == "im_a_user"
