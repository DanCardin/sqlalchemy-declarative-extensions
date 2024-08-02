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
        "tab",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("value", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute('INSERT INTO "tab" (id, value) VALUES (2, 3)')
    op.execute('INSERT INTO "tab" (id, value) VALUES (3, 3)')


def downgrade():
    op.drop_table("tab")
