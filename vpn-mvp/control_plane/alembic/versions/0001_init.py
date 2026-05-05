"""init schema

Revision ID: 0001_init
Revises:
Create Date: 2026-03-18 00:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    user_status = postgresql.ENUM("active", "banned", name="userstatus", create_type=False)
    payment_status = postgresql.ENUM("pending", "confirmed", "failed", name="paymentstatus", create_type=False)
    node_status = postgresql.ENUM("healthy", "unhealthy", "offline", name="nodestatus", create_type=False)
    device_status = postgresql.ENUM("active", "suspended", "banned", "deleted", name="devicestatus", create_type=False)

    postgresql.ENUM("active", "banned", name="userstatus").create(op.get_bind(), checkfirst=True)
    postgresql.ENUM("pending", "confirmed", "failed", name="paymentstatus").create(op.get_bind(), checkfirst=True)
    postgresql.ENUM("healthy", "unhealthy", "offline", name="nodestatus").create(op.get_bind(), checkfirst=True)
    postgresql.ENUM("active", "suspended", "banned", "deleted", name="devicestatus").create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("username", sa.String(length=255)),
        sa.Column("first_name", sa.String(length=255)),
        sa.Column("status", user_status, nullable=False, server_default="active"),
        sa.Column("balance_kopecks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"], unique=True)

    op.create_table(
        "nodes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False, unique=True),
        sa.Column("hostname", sa.String(length=255), nullable=False),
        sa.Column("public_ip", sa.String(length=64), nullable=False),
        sa.Column("country_code", sa.String(length=8), nullable=False),
        sa.Column("city", sa.String(length=128)),
        sa.Column("status", node_status, nullable=False, server_default="healthy"),
        sa.Column("max_clients", sa.Integer(), nullable=False, server_default="300"),
        sa.Column("active_clients", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("api_url", sa.String(length=255), nullable=False),
        sa.Column("token", sa.String(length=255), nullable=False, unique=True),
        sa.Column("agent_version", sa.String(length=64)),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("external_payment_id", sa.String(length=255), unique=True),
        sa.Column("amount_kopecks", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("status", payment_status, nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("confirmed_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "devices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("node_id", sa.Integer(), sa.ForeignKey("nodes.id"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("vpn_ip", sa.String(length=64), nullable=False, unique=True),
        sa.Column("public_key", sa.String(length=255), nullable=False, unique=True),
        sa.Column("private_key_encrypted", sa.String(length=1024), nullable=False),
        sa.Column("status", device_status, nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "device_usage_daily",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("device_id", sa.Integer(), sa.ForeignKey("devices.id"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("rx_bytes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("tx_bytes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.UniqueConstraint("device_id", "date", name="uq_device_usage_daily"),
    )

    op.create_table(
        "billing_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("amount_kopecks", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_type", sa.String(length=64), nullable=False),
        sa.Column("actor_id", sa.String(length=64), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("billing_events")
    op.drop_table("device_usage_daily")
    op.drop_table("devices")
    op.drop_table("payments")
    op.drop_table("nodes")
    op.drop_index("ix_users_telegram_id", table_name="users")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS devicestatus")
    op.execute("DROP TYPE IF EXISTS nodestatus")
    op.execute("DROP TYPE IF EXISTS paymentstatus")
    op.execute("DROP TYPE IF EXISTS userstatus")
