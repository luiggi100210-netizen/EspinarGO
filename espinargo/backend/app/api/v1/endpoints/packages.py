"""
Endpoints para el servicio de encomiendas.

Crear envío, rastrear por código, asignar conductor,
actualizar estado e historial.

Rutas bajo /api/v1/packages/
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_active_user, get_current_driver
from app.models.package import Package, PackageStatus
from app.models.user import User, UserRole
from app.schemas.base import PaginationMeta
from app.schemas.package import (
    PackageListResponse,
    PackagePublic,
    PackageRequest,
    PackageTrackingResponse,
    UpdatePackageStatusRequest,
)
from app.services.package_service import PackageService
from app.utils.serializers import package_to_public

router = APIRouter(
    prefix="/packages",
    tags=["Encomiendas"],
)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=PackagePublic,
    summary="Solicitar envío de encomienda",
)
async def create_package(
    data: PackageRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Crea una nueva encomienda para enviar."""
    return await PackageService.create_package(db, current_user, data)


@router.get(
    "/track/{tracking_code}",
    response_model=PackageTrackingResponse,
    summary="Rastrear encomienda por código",
)
async def track_package(
    tracking_code: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Rastrea una encomienda por su código de seguimiento.
    Este endpoint es público para que el destinatario pueda rastrear.
    """
    try:
        return await PackageService.track_package(db, tracking_code)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/my",
    response_model=PackageListResponse,
    summary="Ver mis encomiendas enviadas",
)
async def get_my_packages(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retorna las encomiendas enviadas por el usuario."""
    return await PackageService.get_my_packages(db, current_user, page, per_page)


@router.get(
    "/pending",
    response_model=PackageListResponse,
    summary="Ver encomiendas disponibles para transportar",
)
async def get_pending_packages(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_driver),
    db: AsyncSession = Depends(get_db),
):
    """Retorna encomiendas en estado PENDING que el conductor puede tomar."""
    offset = (page - 1) * per_page

    result = await db.execute(
        select(Package)
        .where(Package.status == PackageStatus.PENDING)
        .order_by(Package.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    packages = result.scalars().all()

    count_result = await db.execute(
        select(func.count()).select_from(Package).where(Package.status == PackageStatus.PENDING)
    )
    total = count_result.scalar()

    return PackageListResponse(
        packages=[package_to_public(p) for p in packages],
        meta=PaginationMeta.create(total=total, page=page, per_page=per_page),
    )


@router.get(
    "/assigned",
    response_model=PackageListResponse,
    summary="Ver encomiendas activas que estoy transportando",
)
async def get_assigned_packages(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_driver),
    db: AsyncSession = Depends(get_db),
):
    """Retorna las encomiendas activas (ASSIGNED, PICKED_UP, IN_TRANSIT) del conductor."""
    return await PackageService.get_driver_packages(db, current_user, page, per_page)


@router.get(
    "/{package_id}",
    response_model=PackagePublic,
    summary="Ver detalle de una encomienda",
)
async def get_package(
    package_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retorna el detalle de una encomienda. Solo el remitente, el conductor o un admin pueden verla."""
    try:
        package = await PackageService.get_package(db, package_id)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    is_authorized = (
        package.sender_id == current_user.id
        or package.driver_id == current_user.id
        or current_user.role == UserRole.ADMIN
    )
    if not is_authorized:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes acceso a esta encomienda")

    return package_to_public(package)


@router.post(
    "/{package_id}/assign",
    response_model=PackagePublic,
    summary="Asignar encomienda a mi cuenta de conductor",
)
async def assign_package(
    package_id: UUID,
    current_user: User = Depends(get_current_driver),
    db: AsyncSession = Depends(get_db),
):
    """El conductor se asigna una encomienda pendiente."""
    try:
        return await PackageService.assign_package(db, package_id, current_user)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{package_id}/cancel",
    response_model=PackagePublic,
    summary="Cancelar una encomienda",
)
async def cancel_package(
    package_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Cancela una encomienda en estado PENDING o ASSIGNED.
    Solo el remitente o un administrador pueden cancelar.
    """
    try:
        return await PackageService.cancel_package(db, package_id, current_user)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{package_id}/update-status",
    response_model=PackagePublic,
    summary="Actualizar estado de la encomienda",
)
async def update_package_status(
    package_id: UUID,
    data: UpdatePackageStatusRequest,
    current_user: User = Depends(get_current_driver),
    db: AsyncSession = Depends(get_db),
):
    """
    Actualiza el estado de la encomienda (conductor).
    Transiciones válidas:
    ASSIGNED → PICKED_UP
    PICKED_UP → IN_TRANSIT
    IN_TRANSIT → DELIVERED
    """
    try:
        return await PackageService.update_package_status(db, package_id, current_user, data)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
