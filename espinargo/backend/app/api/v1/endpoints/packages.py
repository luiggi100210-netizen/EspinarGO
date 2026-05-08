"""
Endpoints para el servicio de encomiendas.

Crear envío, rastrear por código, asignar conductor,
actualizar estado e historial.

Rutas bajo /api/v1/packages/
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_active_user, get_current_driver
from app.models.user import User
from app.schemas.package import (
    PackageListResponse,
    PackagePublic,
    PackageRequest,
    PackageTrackingResponse,
    UpdatePackageStatusRequest,
)
from app.services.package_service import PackageService

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
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
