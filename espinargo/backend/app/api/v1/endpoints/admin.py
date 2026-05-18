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
from app.schemas.package import PackageListResponse
from app.schemas.trip import TripListResponse
from app.utils.serializers import driver_profile_to_public, package_to_public, trip_to_public

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


@router.get(
    "/users/{user_id}",
    response_model=AdminUserOut,
    summary="Ver detalle de un usuario",
)
async def get_user(
    user_id: UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return AdminUserOut.model_validate(user)


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


@router.get(
    "/drivers/{driver_id}",
    response_model=AdminDriverOut,
    summary="Ver detalle de un conductor",
)
async def get_driver(
    driver_id: UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DriverProfile).where(DriverProfile.user_id == driver_id)
    )
    dp = result.scalar_one_or_none()
    if not dp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil de conductor no encontrado")
    return AdminDriverOut(
        user=AdminUserOut.model_validate(dp.user),
        driver_profile=driver_profile_to_public(dp),
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

    reviewable = (DriverStatus.UNDER_REVIEW, DriverStatus.REJECTED, DriverStatus.SUSPENDED)
    if dp.driver_status not in reviewable:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden revisar conductores en estado 'under_review', 'rejected' o 'suspended'",
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


@router.post(
    "/drivers/{driver_id}/suspend",
    response_model=MessageResponse,
    summary="Suspender privilegios de conducción",
)
async def suspend_driver(
    driver_id: UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Suspende el perfil de conductor sin banear la cuenta de usuario."""
    result = await db.execute(
        select(DriverProfile).where(DriverProfile.user_id == driver_id)
    )
    dp = result.scalar_one_or_none()
    if not dp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil de conductor no encontrado")
    if dp.driver_status == DriverStatus.SUSPENDED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El conductor ya está suspendido")
    dp.driver_status = DriverStatus.SUSPENDED
    return MessageResponse(message="Perfil de conductor suspendido")


@router.get(
    "/trips",
    response_model=TripListResponse,
    summary="Listar todos los viajes",
)
async def list_trips(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    trip_status: Optional[str] = Query(default=None, alias="status", description="searching, negotiating, accepted, in_progress, completed, cancelled"),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    filters = []

    if trip_status:
        try:
            filters.append(Trip.status == TripStatus(trip_status))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Estado inválido: {trip_status}")

    count_result = await db.execute(
        select(func.count()).select_from(Trip).where(*filters)
    )
    total = count_result.scalar()

    result = await db.execute(
        select(Trip)
        .where(*filters)
        .order_by(Trip.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    trips = result.scalars().all()

    return TripListResponse(
        trips=[trip_to_public(t) for t in trips],
        meta=PaginationMeta.create(total=total, page=page, per_page=per_page),
    )


@router.get(
    "/packages",
    response_model=PackageListResponse,
    summary="Listar todas las encomiendas",
)
async def list_packages(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    pkg_status: Optional[str] = Query(default=None, alias="status", description="pending, assigned, picked_up, in_transit, delivered, cancelled"),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    filters = []

    if pkg_status:
        try:
            filters.append(Package.status == PackageStatus(pkg_status))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Estado inválido: {pkg_status}")

    count_result = await db.execute(
        select(func.count()).select_from(Package).where(*filters)
    )
    total = count_result.scalar()

    result = await db.execute(
        select(Package)
        .where(*filters)
        .order_by(Package.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    packages = result.scalars().all()

    return PackageListResponse(
        packages=[package_to_public(p) for p in packages],
        meta=PaginationMeta.create(total=total, page=page, per_page=per_page),
    )


@router.get(
    "/stats",
    response_model=AdminStatsResponse,
    summary="Estadísticas generales del dashboard",
)
async def get_stats(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    user_row = (await db.execute(
        select(
            func.count(User.id).label("total"),
            func.count(User.id).filter(User.status == UserStatus.ACTIVE).label("active"),
            func.count(User.id).filter(User.status == UserStatus.PENDING).label("pending"),
        ).select_from(User)
    )).one()

    driver_row = (await db.execute(
        select(
            func.count(DriverProfile.id).label("total"),
            func.count(DriverProfile.id).filter(DriverProfile.driver_status == DriverStatus.APPROVED).label("approved"),
            func.count(DriverProfile.id).filter(DriverProfile.driver_status == DriverStatus.UNDER_REVIEW).label("pending_review"),
        ).select_from(DriverProfile)
    )).one()

    trip_row = (await db.execute(
        select(
            func.count(Trip.id).label("total"),
            func.count(Trip.id).filter(Trip.status == TripStatus.COMPLETED).label("completed"),
            func.count(Trip.id).filter(Trip.status.in_([
                TripStatus.SEARCHING, TripStatus.NEGOTIATING,
                TripStatus.ACCEPTED, TripStatus.IN_PROGRESS,
            ])).label("active"),
        ).select_from(Trip)
    )).one()

    package_row = (await db.execute(
        select(
            func.count(Package.id).label("total"),
            func.count(Package.id).filter(Package.status == PackageStatus.DELIVERED).label("delivered"),
        ).select_from(Package)
    )).one()

    return AdminStatsResponse(
        total_users=user_row.total,
        active_users=user_row.active,
        pending_users=user_row.pending,
        total_drivers=driver_row.total,
        approved_drivers=driver_row.approved,
        pending_review_drivers=driver_row.pending_review,
        total_trips=trip_row.total,
        completed_trips=trip_row.completed,
        active_trips=trip_row.active,
        total_packages=package_row.total,
        delivered_packages=package_row.delivered,
    )
