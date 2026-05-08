"""
Servicio de viajes — lógica de negocio del flujo InDrive.

Pasajero solicita → conductores hacen ofertas →
pasajero elige → viaje en curso → viaje completado.

Los endpoints solo orquestan HTTP; toda la lógica vive aquí.
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trip import PaymentMethod, Trip, TripCancelReason, TripOffer, TripStatus
from app.models.user import User, UserRole
from app.schemas.base import PaginationMeta
from app.schemas.trip import (
    AcceptOfferRequest,
    TripListResponse,
    TripOfferPublic,
    TripOfferRequest,
    TripPublic,
    TripRequest,
    UpdateTripStatusRequest,
)
from app.schemas.user import UserPublicOut
from app.utils.serializers import driver_profile_to_public, trip_to_public
from app.websockets.manager import manager


class TripService:
    @staticmethod
    async def create_trip(db: AsyncSession, passenger: User, data: TripRequest) -> TripPublic:
        trip = Trip(
            passenger_id=passenger.id,
            origin_address=data.origin_address,
            origin_lat=data.origin_lat,
            origin_lng=data.origin_lng,
            dest_address=data.dest_address,
            dest_lat=data.dest_lat,
            dest_lng=data.dest_lng,
            proposed_price=data.proposed_price,
            payment_method=PaymentMethod(data.payment_method),
            status=TripStatus.SEARCHING,
        )
        db.add(trip)
        await db.commit()

        result = trip_to_public(trip)
        await manager.broadcast_to_drivers({
            "type": "new_trip",
            "trip": result.model_dump(mode="json"),
        })
        return result

    @staticmethod
    async def get_trip_history(
        db: AsyncSession,
        user: User,
        page: int,
        per_page: int,
    ) -> TripListResponse:
        status_filter = Trip.status.in_([TripStatus.COMPLETED, TripStatus.CANCELLED])

        if user.role == UserRole.ADMIN:
            where = status_filter
        elif user.role == UserRole.DRIVER:
            where = and_(Trip.driver_id == user.id, status_filter)
        else:
            where = and_(Trip.passenger_id == user.id, status_filter)

        total = (
            await db.execute(select(func.count()).select_from(Trip).where(where))
        ).scalar()

        trips = (
            await db.execute(
                select(Trip)
                .where(where)
                .order_by(Trip.created_at.desc())
                .offset((page - 1) * per_page)
                .limit(per_page)
            )
        ).scalars().all()

        return TripListResponse(
            trips=[trip_to_public(t) for t in trips],
            meta=PaginationMeta.create(total=total, page=page, per_page=per_page),
        )

    @staticmethod
    async def get_active_trip(db: AsyncSession, passenger: User) -> TripPublic | None:
        result = await db.execute(
            select(Trip)
            .where(
                Trip.passenger_id == passenger.id,
                Trip.status.in_([
                    TripStatus.SEARCHING,
                    TripStatus.NEGOTIATING,
                    TripStatus.ACCEPTED,
                    TripStatus.IN_PROGRESS,
                ]),
            )
            .order_by(Trip.created_at.desc())
            .limit(1)
        )
        trip = result.scalar_one_or_none()
        return trip_to_public(trip) if trip else None

    @staticmethod
    async def get_trip_offers(
        db: AsyncSession,
        trip_id: UUID,
        passenger: User,
    ) -> list[TripOfferPublic]:
        trip = await db.get(Trip, trip_id)

        if not trip:
            raise ValueError("Viaje no encontrado")
        if trip.passenger_id != passenger.id:
            raise PermissionError("No tienes acceso a este viaje")

        now = datetime.now(timezone.utc)
        offers = (
            await db.execute(
                select(TripOffer).where(
                    TripOffer.trip_id == trip_id,
                    TripOffer.is_accepted == False,
                    TripOffer.expires_at > now,
                )
            )
        ).scalars().all()

        return [
            TripOfferPublic(
                id=offer.id,
                driver=UserPublicOut.model_validate(offer.driver),
                driver_profile=driver_profile_to_public(
                    offer.driver.driver_profile if offer.driver else None
                ),
                offered_price=offer.offered_price,
                message=offer.message,
                is_accepted=offer.is_accepted,
                expires_at=offer.expires_at,
                created_at=offer.created_at,
            )
            for offer in offers
        ]

    @staticmethod
    async def create_offer(
        db: AsyncSession,
        driver: User,
        data: TripOfferRequest,
    ) -> TripOfferPublic:
        trip = await db.get(Trip, data.trip_id)

        if not trip:
            raise ValueError("Viaje no encontrado")
        if trip.status not in (TripStatus.SEARCHING, TripStatus.NEGOTIATING):
            raise ValueError("Este viaje ya no acepta ofertas")

        existing = (
            await db.execute(
                select(TripOffer).where(
                    TripOffer.trip_id == data.trip_id,
                    TripOffer.driver_id == driver.id,
                    TripOffer.is_accepted == False,
                )
            )
        ).scalar_one_or_none()

        if existing:
            raise ValueError("Ya tienes una oferta activa en este viaje")

        offer = TripOffer(
            trip_id=data.trip_id,
            driver_id=driver.id,
            offered_price=data.offered_price,
            message=data.message,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=2),
        )

        if trip.status == TripStatus.SEARCHING:
            trip.status = TripStatus.NEGOTIATING

        db.add(offer)
        await db.commit()

        result = TripOfferPublic(
            id=offer.id,
            driver=UserPublicOut.model_validate(driver),
            driver_profile=driver_profile_to_public(driver.driver_profile),
            offered_price=offer.offered_price,
            message=offer.message,
            is_accepted=offer.is_accepted,
            expires_at=offer.expires_at,
            created_at=offer.created_at,
        )

        await manager.broadcast_to_trip(
            data.trip_id,
            {
                "type": "new_offer",
                "offer_id": str(offer.id),
                "offered_price": offer.offered_price,
                "driver_name": driver.full_name,
                "expires_at": offer.expires_at.isoformat(),
            },
        )

        return result

    @staticmethod
    async def accept_offer(
        db: AsyncSession,
        trip_id: UUID,
        data: AcceptOfferRequest,
        passenger: User,
    ) -> TripPublic:
        trip = await db.get(Trip, trip_id)

        if not trip:
            raise ValueError("Viaje no encontrado")
        if trip.passenger_id != passenger.id:
            raise PermissionError("No tienes acceso a este viaje")

        offer = await db.get(TripOffer, data.offer_id)

        if not offer or offer.trip_id != trip_id:
            raise ValueError("Oferta no encontrada")

        now = datetime.now(timezone.utc)
        if offer.expires_at.astimezone(timezone.utc) < now:
            raise ValueError("Esta oferta ya expiró")

        offer.is_accepted = True
        trip.driver_id = offer.driver_id
        trip.final_price = offer.offered_price
        trip.status = TripStatus.ACCEPTED
        trip.accepted_at = now

        await db.commit()

        await manager.send_to_driver(
            offer.driver_id,
            {"type": "offer_accepted", "trip_id": str(trip_id)},
        )

        return trip_to_public(trip)

    @staticmethod
    async def start_trip(db: AsyncSession, trip_id: UUID, driver: User) -> TripPublic:
        trip = await db.get(Trip, trip_id)

        if not trip:
            raise ValueError("Viaje no encontrado")
        if trip.driver_id != driver.id:
            raise PermissionError("No tienes acceso a este viaje")
        if trip.status != TripStatus.ACCEPTED:
            raise ValueError("El viaje no puede iniciarse aún")

        trip.status = TripStatus.IN_PROGRESS
        trip.started_at = datetime.now(timezone.utc)
        await db.commit()

        await manager.broadcast_to_trip(trip_id, {"type": "trip_update", "status": "in_progress"})
        return trip_to_public(trip)

    @staticmethod
    async def complete_trip(db: AsyncSession, trip_id: UUID, driver: User) -> TripPublic:
        trip = await db.get(Trip, trip_id)

        if not trip:
            raise ValueError("Viaje no encontrado")
        if trip.driver_id != driver.id:
            raise PermissionError("No tienes acceso a este viaje")
        if trip.status != TripStatus.IN_PROGRESS:
            raise ValueError("El viaje no está en curso")

        trip.status = TripStatus.COMPLETED
        trip.completed_at = datetime.now(timezone.utc)

        if driver.driver_profile:
            driver.driver_profile.total_trips += 1

        await db.commit()

        await manager.broadcast_to_trip(trip_id, {"type": "trip_update", "status": "completed"})
        return trip_to_public(trip)

    @staticmethod
    async def cancel_trip(
        db: AsyncSession,
        trip_id: UUID,
        user: User,
        data: UpdateTripStatusRequest,
    ) -> TripPublic:
        trip = await db.get(Trip, trip_id)

        if not trip:
            raise ValueError("Viaje no encontrado")

        is_passenger = trip.passenger_id == user.id
        is_driver = trip.driver_id == user.id if trip.driver_id else False

        if not is_passenger and not is_driver:
            raise PermissionError("No tienes acceso a este viaje")

        if trip.status in (TripStatus.COMPLETED, TripStatus.CANCELLED):
            raise ValueError("El viaje ya está completado o cancelado")

        trip.status = TripStatus.CANCELLED
        trip.cancel_reason = (
            TripCancelReason.PASSENGER_CANCEL if is_passenger else TripCancelReason.DRIVER_CANCEL
        )
        trip.cancelled_by = user.id
        trip.cancelled_at = datetime.now(timezone.utc)

        await db.commit()

        await manager.broadcast_to_trip(trip_id, {"type": "trip_update", "status": "cancelled"})
        return trip_to_public(trip)
