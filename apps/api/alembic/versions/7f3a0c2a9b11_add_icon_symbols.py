"""add_icon_symbols

Revision ID: 7f3a0c2a9b11
Revises: d5604b467396
Create Date: 2026-06-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = "7f3a0c2a9b11"
down_revision: Union[str, None] = "d5604b467396"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "icon_symbols",
        sa.Column("id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("term", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("normalized_term", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("symbol", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("symbol_type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("aliases", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_icon_symbols_term"), "icon_symbols", ["term"], unique=False)
    op.create_index(op.f("ix_icon_symbols_normalized_term"), "icon_symbols", ["normalized_term"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_icon_symbols_normalized_term"), table_name="icon_symbols")
    op.drop_index(op.f("ix_icon_symbols_term"), table_name="icon_symbols")
    op.drop_table("icon_symbols")
