"""
Endpoints del panel de administración.

Solo accesibles para usuarios con rol ADMIN.
Rutas bajo /api/v1/admin/
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_admin
from app.models.package import Package, PackageStatus
from app.models.trip import Trip, TripStatus
from app.models.user import DriverProfile, DriverStatus, User, UserRole, UserStatus
from app.schemas.admin import (
    AdminDriverListResponse,
    AdminDriverOut,
    AdminDriverReviewRequest,
    AdminStatsResponse,
    AdminUserListResponse,
    AdminUserOut,
)
from app.schemas.base import MessageResponse, PaginationMeta
from app.utils.serializers import driver_profile_to_public

router = APIRouter(
    prefix="/admin",
    tags=["Administración"],
)


@router.get(
    "/users",
    response_model=AdminUserListResponse,
    summary="Listar todos los usuarios",
)
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    role: Optional[str] = Query(default=None, description="passenger, driver, admin"),
    user_status: Optional[str] = Query(default=None, alias="status", description="pending, active, suspended, banned"),
    search: Optional[str] = Query(default=None, description="Buscar por nombre o teléfono"),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    filters = []

    if role:
        try:
            filters.append(User.role == UserRole(role))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Rol inválido: {role}")

    if user_status:
        try:
            filters.append(User.status == UserStatus(user_status))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Estado inválido: {user_status}")

    if search:
        filters.append(
            or_(
                User.full_name.ilike(f"%{search}%"),
                User.phone_number.ilike(f"%{search}%"),
            )
        )

    count_result = await db.execute(
        select(func.count()).select_from(User).where(*filters)
    )
    total = count_result.scalar()

    result = await db.execute(
        select(User)
        .where(*filters)
        .order_by(User.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    users = result.scalars().all()

    return AdminUserListResponse(
        users=[AdminUserOut.model_validate(u) for u in users],
        meta=PaginationMeta.create(total=total, page=page, per_page=per_page),
    )


@router.post(
    "/users/{user_id}/suspend",
    response_model=MessageResponse,
    summary="Suspender usuario",
)
async def suspend_user(
    user_id: UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    if user.id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No puedes suspenderte a ti mismo")
    user.status = UserStatus.SUSPENDED
    return MessageResponse(message=f"Usuario {user.full_name} suspendido")


@router.post(
    "/users/{user_id}/ban",
    response_model=MessageResponse,
    summary="Banear usuario permanentemente",
)
async def ban_user(
    user_id: UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    if user.id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No puedes banearte a ti mismo")
    user.status = UserStatus.BANNED
    return MessageResponse(message=f"Usuario {user.full_name} baneado")


@router.post(
    "/users/{user_id}/activate",
    response_model=MessageResponse,
    summary="Reactivar usuario suspendido o baneado",
)
async def activate_user(
    user_id: UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    user.status = UserStatus.ACTIVE
    return MessageResponse(message=f"Usuario {user.full_name} activado")


@router.get(
    "/drivers",
    response_model=AdminDriverListResponse,
    summary="Listar conductores (filtrable por estado)",
)
async def list_drivers(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    driver_status: Optional[str] = Query(
        default=None,
        description="pending_docs, under_review, approved, rejected, suspended",
    ),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    filters = [User.role == UserRole.DRIVER]

    if driver_status:
        try:
            filters.append(DriverProfile.driver_status == DriverStatus(driver_status))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Estado de conductor inválido: {driver_status}")

    count_result = await db.execute(
        select(func.count())
        .select_from(User)
        .join(DriverProfile, DriverProfile.user_id == User.id)
        .where(*filters)
    )
    total = count_result.scalar()

    result = await db.execute(
        select(User)
        .join(DriverProfile, DriverProfile.user_id == User.id)
        .where(*filters)
        .order_by(User.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    users = result.scalars().all()

    drivers = [
        AdminDriverOut(
            user=AdminUserOut.model_validate(u),
            driver_profile=driver_profile_to_public(u.driver_profile),
        )
        for u in users
        if u.driver_profile
    ]

    return AdminDriverListResponse(
        drivers=drivers,
        meta=PaginationMeta.create(total=total, page=page, per_page=per_page),
    )


@router.post(
    "/drivers/{driver_id}/review",
    response_model=MessageResponse,
    summary="Aprobar o rechazar conductor",
)
async def review_driver(
    driver_id: UUID,
    data: AdminDriverReviewRequest,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DriverProfile).where(DriverProfile.user_id == driver_id)
    )
    dp = result.scalar_one_or_none()

    if not dp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil de conductor no encontrado")

    if dp.driver_status != DriverStatus.UNDER_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden revisar conductores en estado 'under_review'",
        )

    if data.action == "approve":
        dp.driver_status = DriverStatus.APPROVED
        dp.approved_at = datetime.now(timezone.utc)
        dp.approved_by = admin.id
        return MessageResponse(message="Conductor aprobado correctamente")

    if not data.rejection_reason:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Se requiere motivo de rechazo")

    dp.driver_status = DriverStatus.REJECTED
    dp.rejection_reason = data.rejection_reason
    return MessageResponse(message="Conductor rechazado")


@router.get(
    "/stats",
    response_model=AdminStatsResponse,
    summary="Estadísticas generales del dashboard",
)
async def get_stats(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    async def count(query) -> int:
        r = await db.execute(query)
        return r.scalar()

    return AdminStatsResponse(
        total_users=await count(select(func.count()).select_from(User)),
        active_users=await count(select(func.count()).select_from(User).where(User.status == UserStatus.ACTIVE)),
        pending_users=await count(select(func.count()).select_from(User).where(User.status == UserStatus.PENDING)),
        total_drivers=await count(select(func.count()).select_from(DriverProfile)),
        approved_drivers=await count(select(func.count()).select_from(DriverProfile).where(DriverProfile.driver_status == DriverStatus.APPROVED)),
        pending_review_drivers=await count(select(func.count()).select_from(DriverProfile).where(DriverProfile.driver_status == DriverStatus.UNDER_REVIEW)),
        total_trips=await count(select(func.count()).select_from(Trip)),
        completed_trips=await count(select(func.count()).select_from(Trip).where(Trip.status == TripStatus.COMPLETED)),
        active_trips=await count(
            select(func.count()).select_from(Trip).where(
                Trip.status.in_([TripStatus.SEARCHING, TripStatus.NEGOTIATING, TripStatus.ACCEPTED, TripStatus.IN_PROGRESS])
            )
        ),
        total_packages=await count(select(func.count()).select_from(Package)),
        delivered_packages=await count(select(func.count()).select_from(Package).where(Package.status == PackageStatus.DELIVERED)),
    )
