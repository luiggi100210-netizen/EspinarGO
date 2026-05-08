"""
Endpoints para el flujo completo de viajes (lógica InDrive).

Pasajero solicita → conductores hacen ofertas →
pasajero elige → viaje en curso → viaje completado.

Rutas bajo /api/v1/trips/
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import (
    get_current_active_user,
    get_current_driver,
    get_current_passenger,
)
from app.models.user import User
from app.schemas.trip import (
    AcceptOfferRequest,
    TripListResponse,
    TripOfferPublic,
    TripOfferRequest,
    TripPublic,
    TripRequest,
    UpdateTripStatusRequest,
)
from app.services.trip_service import TripService

router = APIRouter(
    prefix="/trips",
    tags=["Viajes"],
)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=TripPublic,
    summary="Solicitar un nuevo viaje",
)
async def create_trip(
    data: TripRequest,
    current_user: User = Depends(get_current_passenger),
    db: AsyncSession = Depends(get_db),
):
    """El pasajero solicita un viaje con origen, destino y precio propuesto."""
    return await TripService.create_trip(db, current_user, data)


@router.get(
    "/history",
    response_model=TripListResponse,
    summary="Ver historial de mis viajes",
)
async def get_trip_history(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Historial de viajes completados o cancelados (como pasajero o conductor)."""
    return await TripService.get_trip_history(db, current_user, page, per_page)


@router.get(
    "/active",
    response_model=TripPublic | None,
    summary="Ver mi viaje activo actual",
)
async def get_active_trip(
    current_user: User = Depends(get_current_passenger),
    db: AsyncSession = Depends(get_db),
):
    """Retorna el viaje activo actual del pasajero si existe."""
    return await TripService.get_active_trip(db, current_user)


@router.get(
    "/{trip_id}/offers",
    response_model=list[TripOfferPublic],
    summary="Ver las ofertas de conductores para mi viaje",
)
async def get_trip_offers(
    trip_id: UUID,
    current_user: User = Depends(get_current_passenger),
    db: AsyncSession = Depends(get_db),
):
    """Retorna las ofertas activas y no expiradas para este viaje."""
    try:
        return await TripService.get_trip_offers(db, trip_id, current_user)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/offer",
    status_code=status.HTTP_201_CREATED,
    response_model=TripOfferPublic,
    summary="Hacer oferta de precio a un viaje",
)
async def create_offer(
    data: TripOfferRequest,
    current_user: User = Depends(get_current_driver),
    db: AsyncSession = Depends(get_db),
):
    """El conductor hace una contraoferta de precio al viaje."""
    try:
        return await TripService.create_offer(db, current_user, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{trip_id}/accept-offer",
    response_model=TripPublic,
    summary="Aceptar la oferta de un conductor",
)
async def accept_offer(
    trip_id: UUID,
    data: AcceptOfferRequest,
    current_user: User = Depends(get_current_passenger),
    db: AsyncSession = Depends(get_db),
):
    """El pasajero acepta una oferta de precio del conductor."""
    try:
        return await TripService.accept_offer(db, trip_id, data, current_user)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{trip_id}/start",
    response_model=TripPublic,
    summary="Iniciar el viaje (conductor llegó al pasajero)",
)
async def start_trip(
    trip_id: UUID,
    current_user: User = Depends(get_current_driver),
    db: AsyncSession = Depends(get_db),
):
    """El conductor inicia el viaje una vez que llegó al pasajero."""
    try:
        return await TripService.start_trip(db, trip_id, current_user)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{trip_id}/complete",
    response_model=TripPublic,
    summary="Marcar viaje como completado",
)
async def complete_trip(
    trip_id: UUID,
    current_user: User = Depends(get_current_driver),
    db: AsyncSession = Depends(get_db),
):
    """El conductor marca el viaje como completado."""
    try:
        return await TripService.complete_trip(db, trip_id, current_user)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{trip_id}/cancel",
    response_model=TripPublic,
    summary="Cancelar un viaje",
)
async def cancel_trip(
    trip_id: UUID,
    data: UpdateTripStatusRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancela un viaje (pasajero o conductor)."""
    try:
        return await TripService.cancel_trip(db, trip_id, current_user, data)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
