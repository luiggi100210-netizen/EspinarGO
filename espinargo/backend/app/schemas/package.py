"""
Schemas para el servicio de encomiendas.

Incluye crear envío, consultar estado y tracking.
"""

from datetime import datetime
from typing import Optional

from pydantic import Field, field_validator
from uuid import UUID

from app.schemas.base import (
    EspinarGoBaseModel,
    PaginationMeta,
    validate_peru_phone,
)
from app.schemas.user import UserPublicOut


class PackageRequest(EspinarGoBaseModel):
    """
    Datos para solicitar un envío de encomienda.
    """

    recipient_name: str = Field(
        ...,
        max_length=150,
        description="Nombre completo de quien recibe el paquete",
    )
    recipient_phone: str = Field(..., description="Teléfono del destinatario")
    delivery_address: str = Field(
        ...,
        max_length=300,
        description="Dirección completa de entrega",
    )
    size: str = Field(
        ...,
        description="Tamaño del paquete",
    )
    description: str = Field(
        ...,
        max_length=500,
        description="Descripción del contenido del paquete",
    )
    is_fragile: bool = Field(
        default=False,
        description="Marcar si el paquete necesita manejo especial",
    )
    payment_method: str = Field(
        default="cash",
        description="Método de pago",
    )

    @field_validator("recipient_phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return validate_peru_phone(v)

    @field_validator("size")
    @classmethod
    def validate_size(cls, v: str) -> str:
        valid_sizes = ["envelope", "small", "medium", "large"]
        if v not in valid_sizes:
            raise ValueError(
                f"El tamaño debe ser: {', '.join(valid_sizes)}. "
                "envelope→sobres, small→cajas hasta 30cm, "
                "medium→cajas hasta 60cm, large→cajas más grandes"
            )
        return v

    @field_validator("payment_method")
    @classmethod
    def validate_payment(cls, v: str) -> str:
        valid_methods = ["cash", "yape", "plin"]
        if v not in valid_methods:
            raise ValueError(
                f"El método de pago debe ser: {', '.join(valid_methods)}"
            )
        return v


class PackagePublic(EspinarGoBaseModel):
    """
    Datos del paquete para mostrar al cliente.
    """

    id: UUID
    tracking_code: str = Field(..., description="Código único de seguimiento")
    sender: Optional[UserPublicOut]
    driver: Optional[UserPublicOut]
    recipient_name: str
    recipient_phone: str
    delivery_address: str
    size: str
    description: str
    is_fragile: bool
    status: str
    price: Optional[str]
    payment_method: str
    created_at: datetime
    picked_up_at: Optional[datetime]
    delivered_at: Optional[datetime]


class PackageTrackingEvent(EspinarGoBaseModel):
    """
    Un evento en el historial de tracking.
    """

    status: str = Field(..., description="Estado en ese momento")
    description: str = Field(..., description="Mensaje legible del evento")
    created_at: datetime = Field(..., description="Cuándo ocurrió")


class PackageTrackingResponse(EspinarGoBaseModel):
    """
    Respuesta completa del tracking con historial.
    """

    package: PackagePublic = Field(..., description="Datos actuales del paquete")
    tracking_history: list[PackageTrackingEvent] = Field(
        ...,
        description="Historial completo (se muestra como timeline en la app)",
    )


class PackageListResponse(EspinarGoBaseModel):
    """
    Lista paginada de encomiendas.
    """

    packages: list[PackagePublic]
    meta: PaginationMeta


class UpdatePackageStatusRequest(EspinarGoBaseModel):
    """
    Actualizar estado de la encomienda (conductor).
    """

    status: str = Field(..., description="Nuevo estado: picked_up, in_transit, delivered")
    description: Optional[str] = Field(
        default=None,
        max_length=300,
        description="Descripción personalizada del evento (opcional)",
    )

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid_statuses = ["picked_up", "in_transit", "delivered"]
        if v not in valid_statuses:
            raise ValueError(
                f"El estado debe ser: {', '.join(valid_statuses)}"
            )
        return v