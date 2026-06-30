"""add_stories

Revision ID: a9c4f1d2e8b7
Revises: 7f3a0c2a9b11
Create Date: 2026-06-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = "a9c4f1d2e8b7"
down_revision: Union[str, None] = "7f3a0c2a9b11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "stories",
        sa.Column("id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("teacher_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("content", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("audio_options", sa.JSON(), nullable=True),
        sa.Column("image_options", sa.JSON(), nullable=True),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["teacher_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.add_column("activities", sa.Column("story_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.create_foreign_key("fk_activities_story_id_stories", "activities", "stories", ["story_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_activities_story_id_stories", "activities", type_="foreignkey")
    op.drop_column("activities", "story_id")
    op.drop_table("stories")
