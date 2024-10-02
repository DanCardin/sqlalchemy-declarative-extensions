"""empty message

Revision ID: a63ad8efc2f4
Revises:
Create Date: 2022-11-07 11:31:40.736066

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a63ad8efc2f4"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "foo",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Unicode(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("foo")
