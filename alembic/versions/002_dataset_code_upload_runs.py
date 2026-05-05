# -*- coding: utf-8 -*-
"""Add data_entries.dataset_code + unique key; create upload_runs audit table."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002_dataset"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_UX = "ux_data_entry_variant"
_OLD_UX_COLS = ["uploader_name", "version", "indicator_name", "year", "month", "quarter"]
_NEW_UX_COLS = ["uploader_name", "version", "indicator_name", "year", "month", "quarter", "dataset_code"]


def upgrade() -> None:
    op.add_column(
        "data_entries",
        sa.Column("dataset_code", sa.String(64), nullable=False, server_default=""),
    )
    op.drop_index(_UX, table_name="data_entries")
    op.create_index(_UX, "data_entries", _NEW_UX_COLS, unique=True)

    op.create_table(
        "upload_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("uploader_name", sa.Text(), nullable=False),
        sa.Column("version", sa.Text(), nullable=False),
        sa.Column("dataset_code", sa.String(64), nullable=False, server_default=""),
        sa.Column("file_name", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("upload_runs")
    op.drop_index(_UX, table_name="data_entries")
    op.create_index(_UX, "data_entries", _OLD_UX_COLS, unique=True)
    op.drop_column("data_entries", "dataset_code")
