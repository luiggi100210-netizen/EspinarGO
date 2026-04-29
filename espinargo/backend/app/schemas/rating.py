"""
Schemas para el sistema de calificaciones mutuas.

Tras cada viaje, pasajero y conductor se califican.
"""

from datetime import datetime

from pydantic import Field, field_validator
from uuid import UUID

from app.schemas.base import EspinarGoBaseModel, validate_score
from app.schemas.user import UserPublicOut


class RatingRequest(EspinarGoBaseModel):
    """
    Datos para calificar después de un viaje.
    """

    trip_id: UUID = Field(..., description="Qué viaje se está calificando")
    score: int = Field(
        ...,
        ge=1,
        le=5,
        description="Calificación de 1 a 5 estrellas",
    )
    comment: str = Field(
        default=None,
        max_length=500,
        description="Comentario opcional sobre el viaje",
    )

    @field_validator("score")
    @classmethod
    def validate_rating_score(cls, v: int) -> int:
        return validate_score(v)


class RatingPublic(EspinarGoBaseModel):
    """
    Calificación para mostrar en el perfil.
    """

    id: UUID
    score: int
    comment: str | None
    rating_type: str
    created_at: datetime
    rater: UserPublicOut = Field(..., description="Quién calificó")


class RatingSummary(EspinarGoBaseModel):
    """
    Resumen de calificaciones de un usuario.
    """

    average_score: float = Field(..., description="Promedio redondeado a 1 decimal")
    total_ratings: int = Field(..., description="Cuántas calificaciones tiene")
    five_stars: int = Field(..., description="Cantidad de calificaciones de 5")
    four_stars: int = Field(..., description="Cantidad de 4")
    three_stars: int = Field(..., description="Cantidad de 3")
    two_stars: int = Field(..., description="Cantidad de 2")
    one_star: int = Field(..., description="Cantidad de 1")