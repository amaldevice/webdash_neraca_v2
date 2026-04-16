# -*- coding: utf-8 -*-
"""Initial schema: data_entries only."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "data_entries",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("uploader_name", sa.Text(), nullable=False),
        sa.Column("version", sa.Text(), nullable=False),
        sa.Column("template_type", sa.Text(), nullable=True),
        sa.Column("data_type", sa.Text(), nullable=True),
        sa.Column("time_period", sa.Text(), nullable=True),
        sa.Column("indicator_name", sa.Text(), nullable=False),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column("unit", sa.Text(), nullable=True),
        sa.Column("region_code", sa.Text(), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("month", sa.Integer(), nullable=True),
        sa.Column("quarter", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ux_data_entry_variant",
        "data_entries",
        ["uploader_name", "version", "indicator_name", "year", "month", "quarter"],
        unique=True,
    )
def downgrade() -> None:
    op.drop_index("ux_data_entry_variant", table_name="data_entries")
    op.drop_table("data_entries")
