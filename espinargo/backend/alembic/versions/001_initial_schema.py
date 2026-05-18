"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-04-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("full_name", sa.String(150), nullable=False),
        sa.Column("phone_number", sa.String(20), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("phone_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("role", sa.Enum("passenger", "driver", "admin", name="userrole"), nullable=False),
        sa.Column("status", sa.Enum("pending", "active", "suspended", "banned", name="userstatus"), nullable=False),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("google_id", sa.String(100), nullable=True),
        sa.Column("facebook_id", sa.String(100), nullable=True),
        sa.Column("device_token", sa.String(500), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("preferred_lang", sa.String(5), nullable=False, server_default="es"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("phone_number"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("google_id"),
        sa.UniqueConstraint("facebook_id"),
    )
    op.create_index("ix_users_phone_number", "users", ["phone_number"])
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token", sa.String(500), nullable=False),
        sa.Column("is_revoked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_token", "refresh_tokens", ["token"])

    op.create_table(
        "otp_codes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(6), nullable=False),
        sa.Column("purpose", sa.String(50), nullable=False),
        sa.Column("is_used", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_otp_codes_user_id", "otp_codes", ["user_id"])

    op.create_table(
        "driver_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vehicle_type", sa.Enum("mototaxi", "car", name="vehicletype"), nullable=True),
        sa.Column("vehicle_brand", sa.String(100), nullable=True),
        sa.Column("vehicle_model", sa.String(100), nullable=True),
        sa.Column("vehicle_year", sa.Integer(), nullable=True),
        sa.Column("vehicle_color", sa.String(50), nullable=True),
        sa.Column("vehicle_plate", sa.String(20), nullable=True),
        sa.Column("vehicle_seats", sa.Integer(), nullable=True, server_default="3"),
        sa.Column("vehicle_photo_url", sa.String(500), nullable=True),
        sa.Column("dni_front_url", sa.String(500), nullable=True),
        sa.Column("dni_back_url", sa.String(500), nullable=True),
        sa.Column("license_url", sa.String(500), nullable=True),
        sa.Column("soat_url", sa.String(500), nullable=True),
        sa.Column("property_card_url", sa.String(500), nullable=True),
        sa.Column("selfie_url", sa.String(500), nullable=True),
        sa.Column("driver_status", sa.Enum("pending_docs", "under_review", "approved", "rejected", "suspended", name="driverstatus"), nullable=False),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("total_trips", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rating", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("rating_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_online", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("current_lat", sa.String(20), nullable=True),
        sa.Column("current_lng", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
        sa.UniqueConstraint("vehicle_plate"),
    )
    op.create_index("ix_driver_profiles_user_id", "driver_profiles", ["user_id"])

    op.create_table(
        "trips",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("passenger_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("driver_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("origin_address", sa.String(500), nullable=False),
        sa.Column("origin_lat", sa.String(20), nullable=False),
        sa.Column("origin_lng", sa.String(20), nullable=False),
        sa.Column("dest_address", sa.String(500), nullable=False),
        sa.Column("dest_lat", sa.String(20), nullable=False),
        sa.Column("dest_lng", sa.String(20), nullable=False),
        sa.Column("proposed_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("final_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("status", sa.Enum("searching", "negotiating", "accepted", "in_progress", "completed", "cancelled", name="tripstatus"), nullable=False),
        sa.Column("payment_method", sa.String(20), nullable=False),
        sa.Column("distance_km", sa.Numeric(8, 2), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("cancel_reason", sa.Enum("passenger_cancel", "driver_cancel", "timeout", "admin_cancel", name="tripcancelreason"), nullable=True),
        sa.Column("cancelled_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["passenger_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["driver_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_trips_passenger_id", "trips", ["passenger_id"])
    op.create_index("ix_trips_driver_id", "trips", ["driver_id"])
    op.create_index("ix_trips_status", "trips", ["status"])

    op.create_table(
        "trip_offers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("trip_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("driver_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("offered_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("is_accepted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["driver_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_trip_offers_trip_id", "trip_offers", ["trip_id"])
    op.create_index("ix_trip_offers_driver_id", "trip_offers", ["driver_id"])

    op.create_table(
        "packages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sender_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("driver_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("tracking_code", sa.String(30), nullable=False),
        sa.Column("recipient_name", sa.String(150), nullable=False),
        sa.Column("recipient_phone", sa.String(20), nullable=False),
        sa.Column("delivery_address", sa.String(500), nullable=False),
        sa.Column("size", sa.String(20), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_fragile", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("status", sa.Enum("pending", "assigned", "picked_up", "in_transit", "delivered", "cancelled", name="packagestatus"), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=True),
        sa.Column("payment_method", sa.String(20), nullable=False),
        sa.Column("picked_up_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["sender_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["driver_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tracking_code"),
    )
    op.create_index("ix_packages_sender_id", "packages", ["sender_id"])
    op.create_index("ix_packages_tracking_code", "packages", ["tracking_code"])

    op.create_table(
        "package_tracking",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("package_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.Enum("pending", "assigned", "picked_up", "in_transit", "delivered", "cancelled", name="packagestatus"), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["package_id"], ["packages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_package_tracking_package_id", "package_tracking", ["package_id"])

    op.create_table(
        "ratings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("trip_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rater_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rated_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rating_type", sa.Enum("passenger_to_driver", "driver_to_passenger", name="ratingtype"), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["rater_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["rated_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("trip_id", "rater_id", "rating_type", name="uq_rating_per_trip_user_type"),
    )
    op.create_index("ix_ratings_trip_id", "ratings", ["trip_id"])
    op.create_index("ix_ratings_rater_id", "ratings", ["rater_id"])
    op.create_index("ix_ratings_rated_id", "ratings", ["rated_id"])


def downgrade() -> None:
    op.drop_table("ratings")
    op.drop_table("package_tracking")
    op.drop_table("packages")
    op.drop_table("trip_offers")
    op.drop_table("trips")
    op.drop_table("driver_profiles")
    op.drop_table("otp_codes")
    op.drop_table("refresh_tokens")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS ratingtype")
    op.execute("DROP TYPE IF EXISTS packagestatus")
    op.execute("DROP TYPE IF EXISTS tripcancelreason")
    op.execute("DROP TYPE IF EXISTS tripstatus")
    op.execute("DROP TYPE IF EXISTS driverstatus")
    op.execute("DROP TYPE IF EXISTS vehicletype")
    op.execute("DROP TYPE IF EXISTS userstatus")
    op.execute("DROP TYPE IF EXISTS userrole")
