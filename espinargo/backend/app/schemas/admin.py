"""
Schemas del panel de administración.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.base import EspinarGoBaseModel, PaginationMeta
from app.schemas.user import DriverProfilePublic


class AdminUserOut(EspinarGoBaseModel):
    """Usuario con campos extendidos para el panel admin."""

    id: UUID
    full_name: str
    phone_number: str
    email: Optional[str]
    role: str
    status: str
    phone_verified: bool
    avatar_url: Optional[str]
    created_at: datetime
    last_seen_at: Optional[datetime]


class AdminUserListResponse(EspinarGoBaseModel):
    users: list[AdminUserOut]
    meta: PaginationMeta


class AdminDriverOut(EspinarGoBaseModel):
    """Conductor con su perfil para revisión admin."""

    user: AdminUserOut
    driver_profile: DriverProfilePublic


class AdminDriverListResponse(EspinarGoBaseModel):
    drivers: list[AdminDriverOut]
    meta: PaginationMeta


class AdminDriverReviewRequest(EspinarGoBaseModel):
    """Aprobar o rechazar un conductor."""

    action: str = Field(..., description="approve o reject")
    rejection_reason: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Obligatorio si action es reject",
    )

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        if v not in ("approve", "reject"):
            raise ValueError("La acción debe ser 'approve' o 'reject'")
        return v


class AdminStatsResponse(EspinarGoBaseModel):
    """Estadísticas generales del dashboard."""

    total_users: int
    active_users: int
    pending_users: int
    total_drivers: int
    approved_drivers: int
    pending_review_drivers: int
    total_trips: int
    completed_trips: int
    active_trips: int
    total_packages: int
    delivered_packages: int
