"""
Modelos para el servicio de viajes de transporte.

Contiene 2 modelos principales:
- Trip: solicitud de viaje de un pasajero
- TripOffer: contraoferta de precio que hace un conductor

La lógica de InDrive funciona así:
1. El pasajero propone un precio
2. Los conductores ven el viaje y pueden hacer contraofertas
3. El pasajero elige哪位conductor acepta (la oferta aceptada se convierte en el precio final)
"""

from datetime import datetime
from enum import Enum as PyEnum
from uuid import uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base_model import BaseModel


# =============================================================================
# ENUMS - Definiciones de tipos enumerados
# =============================================================================


class TripStatus(PyEnum):
    """
    Estado del viaje a lo largo de su ciclo de vida.
    """

    SEARCHING = "searching"
    NEGOTIATING = "negotiating"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TripCancelReason(PyEnum):
    """
    Razón por la cual se canceló un viaje.
    """

    PASSENGER_CANCEL = "passenger_cancel"
    DRIVER_CANCEL = "driver_cancel"
    NO_DRIVER_FOUND = "no_driver_found"
    DRIVER_NOT_ARRIVED = "driver_not_arrived"


class PaymentMethod(PyEnum):
    """
    Método de pago para el viaje.
    """

    CASH = "cash"
    YAPE = "yape"
    PLIN = "plin"


# =============================================================================
# MODELO: Trip - Solicitud de viaje del pasajero
# =============================================================================


class Trip(BaseModel, Base):
    """
    Solicitud de viaje creada por un pasajero.

    El flujo typical es:
    1. SEARCHING: el pasajero publicó el viaje, esperando ofertas
    2. NEGOTIATING: un conductor hizo una contraoferta
    3. ACCEPTED: el pasajero aceptó una oferta
    4. IN_PROGRESS: el conductor ya recogió al pasajero
    5. COMPLETED: el viaje terminó exitosamente
    6. CANCELLED: el viaje se canceló por alguna razón
    """

    __tablename__ = "trips"

    passenger_id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
        index=True,
        doc="quien solicita el viaje",
    )

    driver_id: Mapped[uuid4 | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="quien acepta el viaje, null hasta que alguien acepte",
    )

    origin_address: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
        doc="dirección en texto del punto de recogida, ej: Plaza de Armas, Espinar",
    )

    origin_lat: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="latitud como string para evitar problemas de precisión",
    )

    origin_lng: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="longitud como string para evitar problemas de precisión",
    )

    dest_address: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
        doc="dirección en texto del destino",
    )

    dest_lat: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    dest_lng: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    proposed_price: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        doc="precio en soles propuesto por el pasajero, string para evitar problemas de redondeo",
    )

    final_price: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        doc="precio acordado tras negociación, null hasta que el pasajero acepte una oferta",
    )

    status: Mapped[TripStatus] = mapped_column(
        Enum(TripStatus),
        default=TripStatus.SEARCHING,
        nullable=False,
        index=True,
    )

    payment_method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod),
        default=PaymentMethod.CASH,
        nullable=False,
    )

    cancel_reason: Mapped[TripCancelReason | None] = mapped_column(
        Enum(TripCancelReason),
        nullable=True,
    )

    cancelled_by: Mapped[uuid4 | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        doc="ID del usuario que canceló el viaje",
    )

    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="cuando el conductor aceptó el precio del viaje",
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="cuando el viaje comenzó (conductor llegó al punto de recogida)",
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="cuando el viaje terminó exitosamente",
    )

    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="cuando se canceló el viaje",
    )

    distance_km: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        doc="distancia calculada por Google Maps en km",
    )

    duration_minutes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="tiempo estimado en minutos",
    )

    passenger: Mapped["User"] = relationship(
        "User",
        foreign_keys=[passenger_id],
        lazy="selectin",
    )

    driver: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[driver_id],
        lazy="selectin",
    )

    offers: Mapped[list["TripOffer"]] = relationship(
        "TripOffer",
        back_populates="trip",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    ratings: Mapped[list["Rating"]] = relationship(
        "Rating",
        back_populates="trip",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def is_active(self) -> bool:
        """Retorna True si el viaje está en curso."""
        return self.status in (
            TripStatus.SEARCHING,
            TripStatus.NEGOTIATING,
            TripStatus.ACCEPTED,
            TripStatus.IN_PROGRESS,
        )

    @property
    def duration_seconds(self) -> int | None:
        """Retorna la duración del viaje en segundos."""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds())
        return None


# =============================================================================
# MODELO: TripOffer - Contraoferta de precio del conductor
# =============================================================================


class TripOffer(BaseModel, Base):
    """
    Contraoferta de precio que hace un conductor a un viaje.

    En el modelo InDrive, el pasajero propone un precio y los conductores
    pueden ofrecer un precio diferente (generalmente menor o igual).
    El pasajero elige cuál oferta aceptar. La oferta aceptada se convierte
    en el precio final del viaje.
    """

    __tablename__ = "trip_offers"

    trip_id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trips.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="viaje al que pertenece esta oferta",
    )

    driver_id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
        index=True,
        doc="conductor que hace la oferta",
    )

    offered_price: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        doc="precio que ofrece el conductor en soles",
    )

    is_accepted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        doc="True cuando el pasajero elige esta oferta",
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="la oferta expira en 2 minutos si no es aceptada",
    )

    message: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        doc="mensaje opcional del conductor, ej: Llego en 3 min",
    )

    trip: Mapped["Trip"] = relationship(
        "Trip",
        back_populates="offers",
        lazy="selectin",
    )

    driver: Mapped["User"] = relationship(
        "User",
        foreign_keys=[driver_id],
        lazy="selectin",
    )


# Importaciones necesarias para evitar errores de tipo
from app.models.user import User
from app.models.rating import Rating