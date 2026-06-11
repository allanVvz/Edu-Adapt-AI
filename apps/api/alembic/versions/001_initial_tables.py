"""Initial tables

Revision ID: 001
Revises:
Create Date: 2026-06-11

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("email", sa.String(), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False, server_default="student"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "student_profiles",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("teacher_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("reading_level", sa.String(), nullable=True),
        sa.Column("autonomy_level", sa.String(), nullable=True),
        sa.Column("main_difficulties", sa.JSON(), nullable=True),
        sa.Column("recommended_strategies", sa.JSON(), nullable=True),
        sa.Column("preferred_modalities", sa.JSON(), nullable=True),
        sa.Column("resources_to_avoid", sa.JSON(), nullable=True),
        sa.Column("accessibility_complexity", sa.String(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "students",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("profile_id", sa.String(), sa.ForeignKey("student_profiles.id"), nullable=True),
        sa.Column("school_year", sa.String(), nullable=True),
        sa.Column("learning_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "teacher_students",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("teacher_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("student_id", sa.String(), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "activities",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("teacher_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("discipline", sa.String(), nullable=True),
        sa.Column("school_year", sa.String(), nullable=True),
        sa.Column("pedagogical_objective", sa.Text(), nullable=True),
        sa.Column("bncc_skill", sa.String(), nullable=True),
        sa.Column("activity_type", sa.String(), nullable=True),
        sa.Column("statement", sa.Text(), nullable=True),
        sa.Column("question", sa.Text(), nullable=True),
        sa.Column("expected_answer", sa.Text(), nullable=True),
        sa.Column("correction_criteria", sa.Text(), nullable=True),
        sa.Column("base_complexity", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("original_modality", sa.String(), nullable=True),
        sa.Column("teacher_notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "activity_adaptations",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("activity_id", sa.String(), sa.ForeignKey("activities.id"), nullable=False),
        sa.Column("student_profile_id", sa.String(), sa.ForeignKey("student_profiles.id"), nullable=True),
        sa.Column("student_id", sa.String(), sa.ForeignKey("students.id"), nullable=True),
        sa.Column("generated_by", sa.String(), nullable=False, server_default="mock"),
        sa.Column("output_data", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("validator_feedback", sa.Text(), nullable=True),
        sa.Column("teacher_feedback", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "student_activity_attempts",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("student_id", sa.String(), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("activity_id", sa.String(), sa.ForeignKey("activities.id"), nullable=False),
        sa.Column("adaptation_id", sa.String(), sa.ForeignKey("activity_adaptations.id"), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="started"),
        sa.Column("raw_response", sa.JSON(), nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("max_score", sa.Float(), nullable=True),
        sa.Column("completion_time_seconds", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "api_keys",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("key_name", sa.String(), nullable=False),
        sa.Column("encrypted_value", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "agent_runs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("adaptation_id", sa.String(), sa.ForeignKey("activity_adaptations.id"), nullable=False),
        sa.Column("agent_name", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("input_data", sa.JSON(), nullable=True),
        sa.Column("output_data", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("model_used", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("agent_runs")
    op.drop_table("api_keys")
    op.drop_table("student_activity_attempts")
    op.drop_table("activity_adaptations")
    op.drop_table("activities")
    op.drop_table("teacher_students")
    op.drop_table("students")
    op.drop_table("student_profiles")
    op.drop_index("ix_users_email", "users")
    op.drop_table("users")
