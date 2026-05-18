"""hash otp codes and add admin_cancel reason

Revision ID: 002
Revises: 001
Create Date: 2026-05-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # OTP code column: String(6) plaintext → String(64) SHA-256 hash
    op.alter_column(
        "otp_codes",
        "code",
        existing_type=sa.String(6),
        type_=sa.String(64),
        nullable=False,
    )

    # Add admin_cancel to tripcancelreason enum
    op.execute("ALTER TYPE tripcancelreason ADD VALUE IF NOT EXISTS 'admin_cancel'")


def downgrade() -> None:
    # Truncate hashed codes back to 6 chars (data loss — only for dev rollback)
    op.execute("UPDATE otp_codes SET code = LEFT(code, 6)")
    op.alter_column(
        "otp_codes",
        "code",
        existing_type=sa.String(64),
        type_=sa.String(6),
        nullable=False,
    )
    # PostgreSQL does not support removing enum values; downgrade is a no-op for the enum
