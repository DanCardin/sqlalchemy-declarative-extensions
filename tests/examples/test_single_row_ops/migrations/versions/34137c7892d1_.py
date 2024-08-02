"""empty message

Revision ID: 34137c7892d1
Revises: a63ad8efc2f4
Create Date: 2023-01-04 16:07:48.335881

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "34137c7892d1"
down_revision = "a63ad8efc2f4"
branch_labels = None
depends_on = None


def upgrade():
    op.insert_table_row("tab", {"id": 1, "value": 1})
    op.update_table_row(
        "tab", to_values={"id": 2, "value": 2}, from_values={"id": 2, "value": 3}
    )
    op.delete_table_row("tab", {"id": 3, "value": 3})


def downgrade():
    pass
