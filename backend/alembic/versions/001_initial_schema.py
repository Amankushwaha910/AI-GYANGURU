"""Initial schema — all tables

Revision ID: 001
Revises:
Create Date: 2026-07-23
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── users ─────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=True),
        sa.Column("role", sa.String(20), nullable=False, server_default="student"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_email_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("google_id", sa.String(255), nullable=True, unique=True),
        sa.Column("supabase_id", sa.String(255), nullable=True, unique=True),
        sa.Column("refresh_token_hash", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_google_id", "users", ["google_id"])
    op.create_index("ix_users_email_active", "users", ["email", "is_active"])

    # ── profiles ──────────────────────────────────────────────
    op.create_table(
        "profiles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("education_level", sa.String(100), nullable=True),
        sa.Column("exam_target", sa.String(100), nullable=True),
        sa.Column("preferred_language", sa.String(10), nullable=False, server_default="en"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_profiles_user_id", "profiles", ["user_id"])

    # ── uploads ───────────────────────────────────────────────
    op.create_table(
        "uploads",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("original_filename", sa.String(500), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("file_type", sa.String(20), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("ocr_used", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_uploads_user_id", "uploads", ["user_id"])
    op.create_index("ix_uploads_user_id_created", "uploads", ["user_id", "created_at"])

    # ── summaries ─────────────────────────────────────────────
    op.create_table(
        "summaries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("upload_id", UUID(as_uuid=True), sa.ForeignKey("uploads.id", ondelete="SET NULL"), nullable=True),
        sa.Column("topic", sa.String(500), nullable=False),
        sa.Column("model_used", sa.String(100), nullable=False),
        sa.Column("sections_requested", JSONB(), nullable=False),
        sa.Column("content", JSONB(), nullable=False),
        sa.Column("is_from_file", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("word_count", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_summaries_user_id", "summaries", ["user_id"])
    op.create_index("ix_summaries_user_topic", "summaries", ["user_id", "topic"])
    op.create_index("ix_summaries_user_created", "summaries", ["user_id", "created_at"])

    # ── explanations ──────────────────────────────────────────
    op.create_table(
        "explanations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("upload_id", UUID(as_uuid=True), sa.ForeignKey("uploads.id", ondelete="SET NULL"), nullable=True),
        sa.Column("topic", sa.String(500), nullable=False),
        sa.Column("model_used", sa.String(100), nullable=False),
        sa.Column("content", JSONB(), nullable=False),
        sa.Column("is_from_file", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_explanations_user_id", "explanations", ["user_id"])
    op.create_index("ix_explanations_user_topic", "explanations", ["user_id", "topic"])

    # ── quizzes ───────────────────────────────────────────────
    op.create_table(
        "quizzes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("upload_id", UUID(as_uuid=True), sa.ForeignKey("uploads.id", ondelete="SET NULL"), nullable=True),
        sa.Column("topic", sa.String(500), nullable=False),
        sa.Column("difficulty", sa.String(20), nullable=False, server_default="mixed"),
        sa.Column("category", sa.String(200), nullable=True),
        sa.Column("question_count", sa.Integer(), nullable=False),
        sa.Column("model_used", sa.String(100), nullable=False),
        sa.Column("is_from_file", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_quizzes_user_id", "quizzes", ["user_id"])

    # ── quiz_questions ────────────────────────────────────────
    op.create_table(
        "quiz_questions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("quiz_id", UUID(as_uuid=True), sa.ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("options", JSONB(), nullable=False),
        sa.Column("correct_option", sa.String(1), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("difficulty", sa.String(20), nullable=False),
        sa.Column("category", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_quiz_questions_quiz_id", "quiz_questions", ["quiz_id"])

    # ── quiz_attempts ─────────────────────────────────────────
    op.create_table(
        "quiz_attempts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("quiz_id", UUID(as_uuid=True), sa.ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_questions", sa.Integer(), nullable=False),
        sa.Column("percentage", sa.Float(), nullable=False, server_default="0"),
        sa.Column("time_taken_seconds", sa.Integer(), nullable=True),
        sa.Column("performance_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_quiz_attempts_user_id", "quiz_attempts", ["user_id"])

    # ── quiz_answers ──────────────────────────────────────────
    op.create_table(
        "quiz_answers",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("attempt_id", UUID(as_uuid=True), sa.ForeignKey("quiz_attempts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_id", UUID(as_uuid=True), sa.ForeignKey("quiz_questions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("selected_option", sa.String(1), nullable=True),
        sa.Column("is_correct", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_quiz_answers_attempt_id", "quiz_answers", ["attempt_id"])

    # ── analytics_events ──────────────────────────────────────
    op.create_table(
        "analytics_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("topic", sa.String(500), nullable=False),
        sa.Column("module", sa.String(50), nullable=False),
        sa.Column("resource_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_analytics_user_id", "analytics_events", ["user_id"])
    op.create_index("ix_analytics_user_created", "analytics_events", ["user_id", "created_at"])

    # ── history_items ─────────────────────────────────────────
    op.create_table(
        "history_items",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_type", sa.String(20), nullable=False),
        sa.Column("topic", sa.String(500), nullable=False),
        sa.Column("resource_id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_history_user_id", "history_items", ["user_id"])
    op.create_index("ix_history_user_type", "history_items", ["user_id", "item_type"])

    # ── ai_requests ───────────────────────────────────────────
    op.create_table(
        "ai_requests",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("module", sa.String(50), nullable=False),
        sa.Column("prompt_hash", sa.String(64), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("latency_ms", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── ai_responses ──────────────────────────────────────────
    op.create_table(
        "ai_responses",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("request_id", UUID(as_uuid=True), sa.ForeignKey("ai_requests.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        sa.Column("finish_reason", sa.String(50), nullable=True),
        sa.Column("is_valid_json", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("ai_responses")
    op.drop_table("ai_requests")
    op.drop_table("history_items")
    op.drop_table("analytics_events")
    op.drop_table("quiz_answers")
    op.drop_table("quiz_attempts")
    op.drop_table("quiz_questions")
    op.drop_table("quizzes")
    op.drop_table("explanations")
    op.drop_table("summaries")
    op.drop_table("uploads")
    op.drop_table("profiles")
    op.drop_table("users")
