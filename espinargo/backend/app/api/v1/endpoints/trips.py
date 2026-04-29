"""
Endpoints para el flujo completo de viajes.

Implementa la lógica de negociación de precios de InDrive:
pasajero solicita → conductores hacen ofertas →
pasajero elige → viaje en curso → viaje completado.

Rutas bajo /api/v1/trips/
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import (
    get_current_active_user,
    get_current_driver,
    get_current_passenger,
)
from app.models.trip import Trip, TripCancelReason, TripOffer, TripStatus
from app.models.user import User, UserRole
from app.schemas.base import MessageResponse, PaginationMeta
from app.schemas.trip import (
    AcceptOfferRequest,
    TripListResponse,
    TripOfferPublic,
    TripOfferRequest,
    TripPublic,
    TripRequest,
    UpdateTripStatusRequest,
)
from app.schemas.user import DriverProfilePublic, UserPublicOut

router = APIRouter(
    prefix="/trips",
    tags=["Viajes"],
)


def _trip_to_public(trip: Trip) -> TripPublic:
    return TripPublic(
        id=trip.id,
        passenger=UserPublicOut.model_validate(trip.passenger) if trip.passenger else None,
        driver=UserPublicOut.model_validate(trip.driver) if trip.driver else None,
        origin_address=trip.origin_address,
        dest_address=trip.dest_address,
        proposed_price=trip.proposed_price,
        final_price=trip.final_price,
        status=trip.status.value,
        payment_method=trip.payment_method,
        distance_km=trip.distance_km,
        duration_minutes=trip.duration_minutes,
        created_at=trip.created_at,
        accepted_at=trip.accepted_at,
        started_at=trip.started_at,
        completed_at=trip.completed_at,
    )


def _driver_profile_to_public(driver_profile) -> DriverProfilePublic | None:
    if not driver_profile:
        return None
    return DriverProfilePublic(
        id=driver_profile.id,
        vehicle_type=driver_profile.vehicle_type,
        vehicle_brand=driver_profile.vehicle_brand,
        vehicle_model=driver_profile.vehicle_model,
        vehicle_year=driver_profile.vehicle_year,
        vehicle_color=driver_profile.vehicle_color,
        vehicle_plate=driver_profile.vehicle_plate,
        vehicle_photo_url=driver_profile.vehicle_photo_url,
        driver_status=driver_profile.driver_status.value,
        rating_display=driver_profile.rating_display,
        total_trips=driver_profile.total_trips,
        is_online=driver_profile.is_online,
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
    """
    El pasajero solicita un nuevo viaje especificando origen,
    destino y el precio que ofrece.
    """
    trip = Trip(
        passenger_id=current_user.id,
        origin_address=data.origin_address,
        origin_lat=data.origin_lat,
        origin_lng=data.origin_lng,
        dest_address=data.dest_address,
        dest_lat=data.dest_lat,
        dest_lng=data.dest_lng,
        proposed_price=data.proposed_price,
        payment_method=data.payment_method,
        status=TripStatus.SEARCHING,
    )

    db.add(trip)
    await db.flush()

    return _trip_to_public(trip)


@router.get(
    "/active",
    response_model=TripPublic | None,
    summary="Ver mi viaje activo actual",
)
async def get_active_trip(
    current_user: User = Depends(get_current_passenger),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna el viaje activo actual del pasajero si existe.
    """
    result = await db.execute(
        select(Trip)
        .where(
            Trip.passenger_id == current_user.id,
            Trip.status.in_(
                [TripStatus.SEARCHING, TripStatus.NEGOTIATING, TripStatus.ACCEPTED, TripStatus.IN_PROGRESS]
            ),
        )
        .order_by(Trip.created_at.desc())
        .limit(1)
    )
    trip = result.scalar_one_or_none()

    if not trip:
        return None

    return _trip_to_public(trip)


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
    """
    Retorna las ofertas activas de conductores para este viaje.
    """
    trip = await db.get(Trip, trip_id)

    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Viaje no encontrado",
        )

    if trip.passenger_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes acceso a este viaje",
        )

    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(TripOffer)
        .where(
            TripOffer.trip_id == trip_id,
            TripOffer.is_accepted == False,
            TripOffer.expires_at > now,
        )
    )
    offers = result.scalars().all()

    return [
        TripOfferPublic(
            id=offer.id,
            driver=UserPublicOut.model_validate(offer.driver),
            driver_profile=_driver_profile_to_public(offer.driver.driver_profile if offer.driver else None),
            offered_price=offer.offered_price,
            message=offer.message,
            is_accepted=offer.is_accepted,
            expires_at=offer.expires_at,
            created_at=offer.created_at,
        )
        for offer in offers
    ]


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
    """
    El conductor hace una contraoferta de precio al viaje.
    """
    trip = await db.get(Trip, data.trip_id)

    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Viaje no encontrado",
        )

    if trip.status not in (TripStatus.SEARCHING, TripStatus.NEGOTIATING):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este viaje ya no acepta ofertas",
        )

    existing_offer = await db.execute(
        select(TripOffer).where(
            TripOffer.trip_id == data.trip_id,
            TripOffer.driver_id == current_user.id,
            TripOffer.is_accepted == False,
        )
    )
    if existing_offer.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya tienes una oferta activa en este viaje",
        )

    offer = TripOffer(
        trip_id=data.trip_id,
        driver_id=current_user.id,
        offered_price=data.offered_price,
        message=data.message,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=2),
    )

    if trip.status == TripStatus.SEARCHING:
        trip.status = TripStatus.NEGOTIATING

    db.add(offer)
    await db.flush()

    return TripOfferPublic(
        id=offer.id,
        driver=UserPublicOut.model_validate(current_user),
        driver_profile=_driver_profile_to_public(current_user.driver_profile),
        offered_price=offer.offered_price,
        message=offer.message,
        is_accepted=offer.is_accepted,
        expires_at=offer.expires_at,
        created_at=offer.created_at,
    )


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
    """
    El pasajero acepta una oferta de precio del conductor.
    """
    trip = await db.get(Trip, trip_id)

    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Viaje no encontrado",
        )

    if trip.passenger_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes acceso a este viaje",
        )

    offer = await db.get(TripOffer, data.offer_id)

    if not offer or offer.trip_id != trip_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Oferta no encontrada",
        )

    now = datetime.now(timezone.utc)
    offer_expiry = offer.expires_at if offer.expires_at.tzinfo else offer.expires_at.replace(tzinfo=timezone.utc)
    if offer_expiry < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta oferta ya expiró",
        )

    offer.is_accepted = True
    trip.driver_id = offer.driver_id
    trip.final_price = offer.offered_price
    trip.status = TripStatus.ACCEPTED
    trip.accepted_at = now

    return _trip_to_public(trip)


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
    """
    El conductor inicia el viaje una vez que llegó al pasajero.
    """
    trip = await db.get(Trip, trip_id)

    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Viaje no encontrado",
        )

    if trip.driver_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes acceso a este viaje",
        )

    if trip.status != TripStatus.ACCEPTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El viaje no puede iniciarse aún",
        )

    trip.status = TripStatus.IN_PROGRESS
    trip.started_at = datetime.now(timezone.utc)

    return _trip_to_public(trip)


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
    """
    El conductor marca el viaje como completado.
    """
    trip = await db.get(Trip, trip_id)

    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Viaje no encontrado",
        )

    if trip.driver_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes acceso a este viaje",
        )

    if trip.status != TripStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El viaje no está en curso",
        )

    trip.status = TripStatus.COMPLETED
    trip.completed_at = datetime.now(timezone.utc)

    if current_user.driver_profile:
        current_user.driver_profile.total_trips += 1

    return _trip_to_public(trip)


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
    """
    Cancela un viaje (pasajero o conductor).
    """
    trip = await db.get(Trip, trip_id)

    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Viaje no encontrado",
        )

    is_passenger = trip.passenger_id == current_user.id
    is_driver = trip.driver_id == current_user.id if trip.driver_id else False

    if not is_passenger and not is_driver:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes acceso a este viaje",
        )

    if trip.status in (TripStatus.COMPLETED, TripStatus.CANCELLED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El viaje ya está completado o cancelado",
        )

    cancel_reason = TripCancelReason.PASSENGER_CANCEL if is_passenger else TripCancelReason.DRIVER_CANCEL

    trip.status = TripStatus.CANCELLED
    trip.cancel_reason = cancel_reason
    trip.cancelled_by = current_user.id
    trip.cancelled_at = datetime.now(timezone.utc)

    return _trip_to_public(trip)


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
    """
    Retorna el historial de viajes del usuario (como pasajero o conductor).
    """
    offset = (page - 1) * per_page

    if current_user.role in (UserRole.PASSENGER, UserRole.ADMIN):
        passenger_filter = Trip.passenger_id == current_user.id
    else:
        passenger_filter = None

    if current_user.role in (UserRole.DRIVER, UserRole.ADMIN):
        driver_filter = Trip.driver_id == current_user.id
    else:
        driver_filter = None

    if passenger_filter is not None and driver_filter is not None:
        filter_condition = or_(passenger_filter, driver_filter)
    elif passenger_filter is not None:
        filter_condition = passenger_filter
    else:
        filter_condition = driver_filter

    status_filter = Trip.status.in_([TripStatus.COMPLETED, TripStatus.CANCELLED])

    count_result = await db.execute(
        select(func.count()).select_from(Trip).where(and_(filter_condition, status_filter))
    )
    total = count_result.scalar()

    result = await db.execute(
        select(Trip)
        .where(and_(filter_condition, status_filter))
        .order_by(Trip.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    trips = result.scalars().all()

    meta = PaginationMeta.create(total=total, page=page, per_page=per_page)

    return TripListResponse(trips=[_trip_to_public(t) for t in trips], meta=meta)
