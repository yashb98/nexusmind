"""Initial schema — all 11 Postgres tables.

Revision ID: 001
Revises:
Create Date: 2026-03-15
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. tenants
    op.create_table(
        "tenants",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("plan", sa.String(20), server_default="free"),
        sa.Column("max_agents", sa.Integer, server_default="5"),
        sa.Column("max_conversations_per_day", sa.Integer, server_default="100"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.CheckConstraint("plan IN ('free','pro','enterprise')", name="ck_tenants_plan"),
    )

    # 2. users
    op.create_table(
        "users",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), server_default="member"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )

    # 3. agents
    op.create_table(
        "agents",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", UUID, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("openness", sa.Float, nullable=False),
        sa.Column("conscientiousness", sa.Float, nullable=False),
        sa.Column("extraversion", sa.Float, nullable=False),
        sa.Column("agreeableness", sa.Float, nullable=False),
        sa.Column("neuroticism", sa.Float, nullable=False),
        sa.Column("interests", ARRAY(sa.Text), nullable=False, server_default="{}"),
        sa.Column("communication_style", sa.String(20), server_default="analytical"),
        sa.Column("lora_archetype", sa.String(50)),
        sa.Column("default_privacy_level", sa.Integer, server_default="2"),
        sa.Column("avatar_image_url", sa.String(500)),
        sa.Column("default_trust_for_strangers", sa.Float, server_default="0.2", nullable=False),
        sa.Column("is_mock", sa.Boolean, server_default="false", nullable=False),
        sa.Column("tagline", sa.String(255), nullable=True),
        sa.Column("domain_modifiers", sa.JSON, server_default="{}"),
        sa.Column("personality_confidence", sa.Float, server_default="0.7"),
        sa.Column("questions_answered", sa.Integer, server_default="0"),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("tutor_voice", sa.String(100), server_default="en-GB-SoniaNeural"),
        sa.Column("tutor_avatar_url", sa.String(500), nullable=True),
        sa.Column("tutor_mode_preference", sa.String(20), server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.CheckConstraint("openness BETWEEN 0 AND 1", name="ck_agents_openness"),
        sa.CheckConstraint("conscientiousness BETWEEN 0 AND 1", name="ck_agents_conscientiousness"),
        sa.CheckConstraint("extraversion BETWEEN 0 AND 1", name="ck_agents_extraversion"),
        sa.CheckConstraint("agreeableness BETWEEN 0 AND 1", name="ck_agents_agreeableness"),
        sa.CheckConstraint("neuroticism BETWEEN 0 AND 1", name="ck_agents_neuroticism"),
        sa.CheckConstraint("default_privacy_level BETWEEN 0 AND 5", name="ck_agents_privacy"),
    )

    # 4. permissions
    op.create_table(
        "permissions",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("agent_id", UUID, sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_agent_id", UUID, sa.ForeignKey("agents.id")),
        sa.Column("level", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.UniqueConstraint("agent_id", "target_agent_id", name="uq_permissions_agent_target"),
        sa.CheckConstraint("level BETWEEN 0 AND 5", name="ck_permissions_level"),
    )

    # 4b. connection_requests
    op.create_table(
        "connection_requests",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("from_agent_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("to_agent_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("message", sa.String(500), nullable=True),
        sa.Column("status", sa.String(20), server_default="pending", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("from_agent_id", "to_agent_id"),
    )
    op.create_index("idx_connection_requests_to", "connection_requests", ["to_agent_id", "status"])

    # 5. learner_knowledge
    op.create_table(
        "learner_knowledge",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("topic", sa.String(255), nullable=False),
        sa.Column("bloom_level", sa.Integer, server_default="1"),
        sa.Column("confidence", sa.Float, server_default="0.0"),
        sa.Column("misconceptions", JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("question_count", sa.Integer, server_default="0"),
        sa.Column("correct_count", sa.Integer, server_default="0"),
        sa.Column("last_assessed", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("user_id", "topic", name="uq_learner_knowledge_user_topic"),
        sa.CheckConstraint("bloom_level BETWEEN 1 AND 6", name="ck_learner_bloom"),
    )

    # 6. teachback_sessions
    op.create_table(
        "teachback_sessions",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("insight_id", sa.String(255), nullable=False),
        sa.Column("topic", sa.String(255), nullable=False),
        sa.Column("bloom_level_start", sa.Integer),
        sa.Column("bloom_level_end", sa.Integer),
        sa.Column("turns", sa.Integer, server_default="0"),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("avatar_id", UUID),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
    )

    # 7. verification_decisions
    op.create_table(
        "verification_decisions",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, nullable=False),
        sa.Column("insight_content", sa.Text, nullable=False),
        sa.Column("source_conversation_id", UUID),
        sa.Column("skeptic_score", sa.Float),
        sa.Column("skeptic_reasoning", sa.Text),
        sa.Column("connector_score", sa.Float),
        sa.Column("connector_relations", JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("judge_decision", sa.String(20)),
        sa.Column("judge_reasoning", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.CheckConstraint(
            "judge_decision IN ('accepted','provisional','investigate','rejected')",
            name="ck_verification_decision",
        ),
    )

    # 8. finetune_runs
    op.create_table(
        "finetune_runs",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("run_type", sa.String(10), nullable=False),
        sa.Column("archetype", sa.String(50), nullable=False),
        sa.Column("training_examples", sa.Integer),
        sa.Column("iterations", sa.Integer),
        sa.Column("lora_rank", sa.Integer),
        sa.Column("val_loss_start", sa.Float),
        sa.Column("val_loss_end", sa.Float),
        sa.Column("personality_variance", sa.Float),
        sa.Column("adapter_version", sa.String(50)),
        sa.Column("deployed", sa.Boolean, server_default="false"),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("run_type IN ('micro','full')", name="ck_finetune_run_type"),
    )

    # 9. evolution_proposals
    op.create_table(
        "evolution_proposals",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("proposal_type", sa.String(20)),
        sa.Column("title", sa.String(500)),
        sa.Column("source_url", sa.String(500)),
        sa.Column("relevance_score", sa.Float),
        sa.Column("difficulty_score", sa.Float),
        sa.Column("improvement_score", sa.Float),
        sa.Column("description", sa.Text),
        sa.Column("implementation_plan", sa.Text),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.CheckConstraint(
            "proposal_type IN ('research','code','hyperparameter')",
            name="ck_proposal_type",
        ),
        sa.CheckConstraint(
            "status IN ('pending','approved','rejected','implemented')",
            name="ck_proposal_status",
        ),
    )

    # 10. audit_log
    op.create_table(
        "audit_log",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, nullable=False),
        sa.Column("agent_id", UUID, nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("target_agent_id", UUID),
        sa.Column("permission_level_used", sa.Integer),
        sa.Column("data_category", sa.String(50)),
        sa.Column("langfuse_trace_id", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )

    # 11. scheduler_metrics
    op.create_table(
        "scheduler_metrics",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("mode", sa.String(20)),
        sa.Column("agent_ids", ARRAY(UUID), nullable=False),
        sa.Column("topic", sa.String(255)),
        sa.Column("conversation_id", UUID),
        sa.Column("quality_score", sa.Float),
        sa.Column("duration_seconds", sa.Float),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.CheckConstraint("mode IN ('explore','research','refine')", name="ck_scheduler_mode"),
    )

    # 12. notification_preferences
    op.create_table(
        "notification_preferences",
        sa.Column("user_id", UUID, sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("new_insights", sa.Boolean, server_default="true"),
        sa.Column("connection_requests", sa.Boolean, server_default="true"),
        sa.Column("community_alerts", sa.Boolean, server_default="true"),
        sa.Column("daily_summaries", sa.Boolean, server_default="false"),
        sa.Column("weekly_reports", sa.Boolean, server_default="false"),
    )

    # Indexes
    op.create_index("idx_agents_tenant", "agents", ["tenant_id"])
    op.create_index("idx_knowledge_user", "learner_knowledge", ["user_id"])
    op.create_index("idx_audit_tenant_time", "audit_log", ["tenant_id", sa.text("created_at DESC")])
    op.create_index("idx_finetune_archetype", "finetune_runs", ["archetype", sa.text("completed_at DESC")])
    op.create_index("idx_verification_time", "verification_decisions", [sa.text("created_at DESC")])
    op.create_index("idx_scheduler_time", "scheduler_metrics", [sa.text("created_at DESC")])
    op.create_index("idx_proposals_status", "evolution_proposals", ["status", sa.text("created_at DESC")])

    # ── Social Layer ──────────────────────────────────────────────────

    # Groups
    op.create_table(
        "groups",
        sa.Column("id", sa.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("group_type", sa.String(20), nullable=True),
        sa.Column("created_by", sa.UUID, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("max_members", sa.Integer, server_default="20"),
        sa.Column("is_public", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "group_members",
        sa.Column("id", sa.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("group_id", sa.UUID, sa.ForeignKey("groups.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_id", sa.UUID, sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("role", sa.String(20), server_default="member"),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("group_id", "agent_id"),
    )
    op.create_index("idx_group_members_group", "group_members", ["group_id"])
    op.create_index("idx_group_members_agent", "group_members", ["agent_id"])

    # Events
    op.create_table(
        "events",
        sa.Column("id", sa.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("event_type", sa.String(20), nullable=True),
        sa.Column("created_by", sa.UUID, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("group_id", sa.UUID, sa.ForeignKey("groups.id"), nullable=True),
        sa.Column("status", sa.String(20), server_default="upcoming"),
        sa.Column("max_participants", sa.Integer, server_default="20"),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rules", sa.JSON, server_default="{}"),
        sa.Column("results", sa.JSON, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_events_status", "events", ["status", "starts_at"])

    op.create_table(
        "event_participants",
        sa.Column("id", sa.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("event_id", sa.UUID, sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_id", sa.UUID, sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("team_id", sa.UUID, nullable=True),
        sa.Column("role", sa.String(20), server_default="participant"),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("event_id", "agent_id"),
    )
    op.create_index("idx_event_participants", "event_participants", ["event_id"])

    op.create_table(
        "event_teams",
        sa.Column("id", sa.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("event_id", sa.UUID, sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Feed
    op.create_table(
        "feed_items",
        sa.Column("id", sa.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("item_type", sa.String(30), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("related_agent_ids", sa.ARRAY(sa.UUID), server_default="{}"),
        sa.Column("related_conversation_id", sa.UUID, nullable=True),
        sa.Column("related_group_id", sa.UUID, nullable=True),
        sa.Column("related_event_id", sa.UUID, nullable=True),
        sa.Column("read", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_feed_user_time", "feed_items", ["user_id", sa.text("created_at DESC")])


def downgrade() -> None:
    op.drop_table("feed_items")
    op.drop_table("event_teams")
    op.drop_table("event_participants")
    op.drop_table("events")
    op.drop_table("group_members")
    op.drop_table("groups")
    op.drop_table("notification_preferences")
    op.drop_table("scheduler_metrics")
    op.drop_table("audit_log")
    op.drop_table("evolution_proposals")
    op.drop_table("finetune_runs")
    op.drop_table("verification_decisions")
    op.drop_table("teachback_sessions")
    op.drop_table("learner_knowledge")
    op.drop_table("connection_requests")
    op.drop_table("permissions")
    op.drop_table("agents")
    op.drop_table("users")
    op.drop_table("tenants")
