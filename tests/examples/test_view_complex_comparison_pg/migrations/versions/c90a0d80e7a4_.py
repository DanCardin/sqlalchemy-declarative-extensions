"""empty message

Revision ID: c90a0d80e7a4
Revises:
Create Date: 2023-02-27 17:12:44.745782

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c90a0d80e7a4"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute(sa.text("CREATE SCHEMA wat"))
    op.create_table(
        "foo",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="wat",
    )
    op.create_table(
        "bar",
        sa.Column("foo_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["foo_id"],
            ["wat.foo.id"],
        ),
        sa.PrimaryKeyConstraint("foo_id"),
        schema="wat",
    )
    op.insert_table_row("wat.foo", {"id": 3})


def downgrade():
    op.delete_table_row("wat.foo", {"id": 3})
    op.drop_table("bar", schema="wat")
    op.drop_table("foo", schema="wat")
    op.drop_schema("wat")
