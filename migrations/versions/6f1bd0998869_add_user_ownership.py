"""add user ownership

Revision ID: 6f1bd0998869
Revises: c1e28cda48f2
Create Date: 2026-06-05 22:07:36.330741

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6f1bd0998869'
down_revision: Union[str, Sequence[str], None] = 'c1e28cda48f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("categories", sa.Column("user_id", sa.Integer(), nullable=True))
    op.add_column("goals", sa.Column("user_id", sa.Integer(), nullable=True))
    op.add_column("transactions", sa.Column("user_id", sa.Integer(), nullable=True))

    op.execute("UPDATE categories SET user_id = 2 WHERE user_id IS NULL")
    op.execute("UPDATE goals SET user_id = 2 WHERE user_id IS NULL")
    op.execute("UPDATE transactions SET user_id = 2 WHERE user_id IS NULL")

    op.alter_column("categories", "user_id", existing_type=sa.Integer(), nullable=False)
    op.alter_column("goals", "user_id", existing_type=sa.Integer(), nullable=False)
    op.alter_column("transactions", "user_id", existing_type=sa.Integer(), nullable=False)

    op.create_index("ix_categories_user_id", "categories", ["user_id"], unique=False)
    op.create_index("ix_goals_user_id", "goals", ["user_id"], unique=False)
    op.create_index("ix_transactions_user_id", "transactions", ["user_id"], unique=False)

    op.create_foreign_key(
        "fk_categories_user_id_users",
        "categories",
        "users",
        ["user_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_goals_user_id_users",
        "goals",
        "users",
        ["user_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_transactions_user_id_users",
        "transactions",
        "users",
        ["user_id"],
        ["id"],
    )

    op.execute("ALTER TABLE categories DROP CONSTRAINT IF EXISTS categories_name_key")

    op.create_unique_constraint(
        "uq_categories_user_id_name",
        "categories",
        ["user_id", "name"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("uq_categories_user_id_name", "categories", type_="unique")

    op.drop_constraint("fk_transactions_user_id_users", "transactions", type_="foreignkey")
    op.drop_constraint("fk_goals_user_id_users", "goals", type_="foreignkey")
    op.drop_constraint("fk_categories_user_id_users", "categories", type_="foreignkey")

    op.drop_index("ix_transactions_user_id", table_name="transactions")
    op.drop_index("ix_goals_user_id", table_name="goals")
    op.drop_index("ix_categories_user_id", table_name="categories")

    op.drop_column("transactions", "user_id")
    op.drop_column("goals", "user_id")
    op.drop_column("categories", "user_id")

    op.create_unique_constraint("categories_name_key", "categories", ["name"])