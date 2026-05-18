"""
Schemas para perfiles de usuario y conductores.

Controlan qué datos del usuario se exponen al cliente.
NUNCA exponen el password_hash ni datos internos.
"""

from datetime import datetime
from typing import Optional

from pydantic import Field, field_validator
from uuid import UUID

from app.schemas.base import EspinarGoBaseModel


class UserPublicOut(EspinarGoBaseModel):
    """
    Datos básicos del usuario para respuestas de API.
    """

    id: UUID
    full_name: str
    phone_number: str
    email: Optional[str]
    role: str
    status: str
    phone_verified: bool
    avatar_url: Optional[str]


class UserProfile(EspinarGoBaseModel):
    """
    Perfil completo con más detalles.
    """

    id: UUID
    full_name: str
    phone_number: str
    email: Optional[str]
    role: str
    status: str
    phone_verified: bool
    email_verified: bool
    avatar_url: Optional[str]
    preferred_lang: str
    created_at: datetime
    last_seen_at: Optional[datetime]


class UpdateProfileRequest(EspinarGoBaseModel):
    """
    Campos que el usuario puede actualizar.
    """

    full_name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=150,
    )
    email: Optional[str] = Field(default=None)
    preferred_lang: Optional[str] = Field(
        default=None,
        max_length=5,
        examples=["es", "qu"],
        description="Español o quechua (lengua de Espinar)",
    )

    @field_validator("preferred_lang")
    @classmethod
    def validate_lang(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ("es", "qu"):
            raise ValueError("El idioma debe ser 'es' (español) o 'qu' (quechua)")
        return v

    @field_validator("full_name")
    @classmethod
    def normalize_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return v.strip().title()
        return v


class UpdateAvatarResponse(EspinarGoBaseModel):
    """
    Respuesta tras subir foto de perfil.
    """

    message: str
    avatar_url: str = Field(..., description="URL de Cloudinary de la nueva foto")


class DriverProfilePublic(EspinarGoBaseModel):
    """
    Información del conductor visible para pasajeros.
    """

    id: UUID
    vehicle_type: Optional[str]
    vehicle_brand: Optional[str]
    vehicle_model: Optional[str]
    vehicle_year: Optional[int]
    vehicle_color: Optional[str]
    vehicle_plate: Optional[str]
    vehicle_photo_url: Optional[str]
    driver_status: str
    rating_display: float = Field(
        ...,
        description="Calificación en estrellas (0.0 a 5.0)",
    )
    total_trips: int
    is_online: bool


class UpdateVehicleRequest(EspinarGoBaseModel):
    """
    Datos del vehículo que el conductor puede actualizar.
    """

    vehicle_type: Optional[str] = Field(default=None)
    vehicle_brand: Optional[str] = Field(default=None, max_length=100)
    vehicle_model: Optional[str] = Field(default=None, max_length=100)
    vehicle_year: Optional[int] = Field(default=None)
    vehicle_color: Optional[str] = Field(default=None, max_length=50)
    vehicle_plate: Optional[str] = Field(default=None, max_length=20)
    vehicle_seats: Optional[int] = Field(default=None)

    @field_validator("vehicle_type")
    @classmethod
    def validate_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid_types = ["mototaxi", "car"]
            if v not in valid_types:
                raise ValueError(f"El tipo debe ser: {', '.join(valid_types)}")
        return v

    @field_validator("vehicle_year")
    @classmethod
    def validate_year(cls, v: Optional[int]) -> Optional[int]:
        if v is not None:
            current_year = datetime.now().year
            if v < 1990 or v > current_year:
                raise ValueError(
                    f"El año debe estar entre 1990 y {current_year}"
                )
        return v

    @field_validator("vehicle_plate")
    @classmethod
    def normalize_plate(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return v.strip().upper()
        return v

    @field_validator("vehicle_seats")
    @classmethod
    def validate_seats(cls, v: Optional[int]) -> Optional[int]:
        if v is not None:
            if v < 1 or v > 6:
                raise ValueError("Los asientos deben estar entre 1 y 6")
        return v


class UploadDocumentResponse(EspinarGoBaseModel):
    """
    Respuesta tras subir un documento.
    """

    message: str
    document_type: str = Field(..., description="Qué documento se subió")
    url: str = Field(..., description="URL de Cloudinary del documento")
    driver_status: str = Field(..., description="Nuevo estado del conductor")


class DocumentStatusResponse(EspinarGoBaseModel):
    """
    Estado actual de los documentos del conductor.
    """

    dni_front_url: Optional[str]
    dni_back_url: Optional[str]
    license_url: Optional[str]
    soat_url: Optional[str]
    selfie_url: Optional[str]
    property_card_url: Optional[str]
    vehicle_photo_url: Optional[str]
    driver_status: str
    rejection_reason: Optional[str] = None


class UpdateOnlineStatusRequest(EspinarGoBaseModel):
    """
    Activar o desactivar disponibilidad del conductor.
    """

    is_online: bool = Field(..., description="True para activarse, False para desactivarse")


class UpdateDeviceTokenRequest(EspinarGoBaseModel):
    """
    Token FCM del dispositivo para recibir push notifications.
    """

    device_token: str = Field(..., max_length=500, description="Token FCM del dispositivo")