"""
Schemas para el flujo completo de viajes.

Incluye solicitar viaje, hacer ofertas (lógica InDrive),
actualizar estado y consultar historial.
"""

from datetime import datetime
from typing import Optional

from pydantic import Field, field_validator
from uuid import UUID

from app.schemas.base import (
    EspinarGoBaseModel,
    PaginationMeta,
    validate_price,
)
from app.schemas.user import UserPublicOut, DriverProfilePublic


class TripRequest(EspinarGoBaseModel):
    """
    Datos para solicitar un nuevo viaje.
    """

    origin_address: str = Field(
        ...,
        max_length=300,
        description="Dirección de recogida en texto",
        examples=["Plaza de Armas, Espinar, Cusco"],
    )
    origin_lat: str = Field(..., description="Latitud del punto de origen")
    origin_lng: str = Field(..., description="Longitud del punto de origen")
    dest_address: str = Field(
        ...,
        max_length=300,
        description="Dirección de destino en texto",
    )
    dest_lat: str = Field(..., description="Latitud del destino")
    dest_lng: str = Field(..., description="Longitud del destino")
    proposed_price: str = Field(
        ...,
        description="Precio en soles que ofrece el pasajero",
        examples=["5.00", "8.50"],
    )
    payment_method: str = Field(
        default="cash",
        description="Método de pago",
    )

    @field_validator("origin_lat", "origin_lng", "dest_lat", "dest_lng")
    @classmethod
    def validate_coordinate(cls, v: str) -> str:
        try:
            float(v)
        except (ValueError, TypeError):
            raise ValueError("Coordenada inválida")
        return v

    @field_validator("proposed_price")
    @classmethod
    def validate_price_value(cls, v: str) -> str:
        return validate_price(v)

    @field_validator("payment_method")
    @classmethod
    def validate_payment(cls, v: str) -> str:
        valid_methods = ["cash", "yape", "plin"]
        if v not in valid_methods:
            raise ValueError(
                f"El método de pago debe ser: {', '.join(valid_methods)}"
            )
        return v


class TripPublic(EspinarGoBaseModel):
    """
    Datos de un viaje para mostrar al cliente.
    """

    id: UUID
    passenger: Optional[UserPublicOut]
    driver: Optional[UserPublicOut]
    origin_address: str
    dest_address: str
    proposed_price: str
    final_price: Optional[str]
    status: str
    payment_method: str
    distance_km: Optional[str]
    duration_minutes: Optional[int]
    created_at: datetime
    accepted_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


class TripOfferRequest(EspinarGoBaseModel):
    """
    Contraoferta de precio que hace el conductor.
    """

    trip_id: UUID = Field(..., description="A qué viaje hace la oferta")
    offered_price: str = Field(..., description="Precio que ofrece el conductor")
    message: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Mensaje opcional del conductor",
        examples=["Llego en 3 minutos", "Acepto por S/6"],
    )

    @field_validator("offered_price")
    @classmethod
    def validate_price_value(cls, v: str) -> str:
        return validate_price(v)


class TripOfferPublic(EspinarGoBaseModel):
    """
    Oferta visible para el pasajero.
    """

    id: UUID
    driver: UserPublicOut
    driver_profile: Optional[DriverProfilePublic]
    offered_price: str
    message: Optional[str]
    is_accepted: bool
    expires_at: datetime
    created_at: datetime


class AcceptOfferRequest(EspinarGoBaseModel):
    """
    El pasajero elige una oferta de conductor.
    """

    offer_id: UUID = Field(..., description="ID de la oferta que el pasajero acepta")


class UpdateTripStatusRequest(EspinarGoBaseModel):
    """
    Actualizar el estado del viaje en curso.
    """

    status: str = Field(..., description="Nuevo estado del viaje")
    cancel_reason: Optional[str] = Field(default=None)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid_statuses = [
            "searching",
            "negotiating",
            "accepted",
            "in_progress",
            "completed",
            "cancelled",
        ]
        if v not in valid_statuses:
            raise ValueError(f"El estado debe ser: {', '.join(valid_statuses)}")
        return v


class TripListResponse(EspinarGoBaseModel):
    """
    Lista paginada de viajes.
    """

    trips: list[TripPublic]
    meta: PaginationMeta


class DriverEarningsResponse(EspinarGoBaseModel):
    """
    Resumen de ganancias del conductor.
    """

    total_earnings: str
    total_trips: int
    this_week_earnings: str
    this_month_earnings: str