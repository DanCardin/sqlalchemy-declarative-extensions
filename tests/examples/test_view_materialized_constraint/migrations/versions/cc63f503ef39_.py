"""empty message

Revision ID: cc63f503ef39
Revises:
Create Date: 2023-02-27 17:09:42.278388

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "cc63f503ef39"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "foo",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("num", sa.Integer(), nullable=False),
        sa.Column("num2", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("foo")
