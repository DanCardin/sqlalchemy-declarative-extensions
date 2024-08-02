"""empty message

Revision ID: a63ad8efc2f4
Revises:
Create Date: 2022-11-07 11:31:40.736066

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "a63ad8efc2f4"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_role("read")
    op.update_role("write", login=True)
    op.drop_role("app")


def downgrade():
    op.drop_foo("read")
    op.update_role("write", login=False)
    op.create_role("app")
