"""empty message

Revision ID: 0522a3309c12
Revises:
Create Date: 2022-11-22 07:49:21.709903

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0522a3309c12"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_role(
        "o2_read",
    )
    op.create_role(
        "o2_write",
    )
    op.create_role(
        "o1_app",
        in_roles=["o2_read", "o2_write"],
        superuser=False,
        createdb=False,
        createrole=False,
        inherit=True,
        login=False,
        replication=False,
        bypass_rls=False,
    )


def downgrade():
    op.drop_role("o1_app")
    op.drop_role("o2_write")
    op.drop_role("o2_read")
