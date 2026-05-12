"""
Modelos para calificaciones mutuas entre usuarios.

El modelo Rating permite que pasajeros y conductores se califiquen
después de cada viaje. También aplica a entregas de encomiendas.

Cada viaje puede tener hasta 2 calificaciones:
- Una del pasajero al conductor (passenger_to_driver)
- Una del conductor al pasajero (driver_to_passenger)
"""

from enum import Enum as PyEnum
from uuid import uuid4

from sqlalchemy import Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base_model import BaseModel


# =============================================================================
# ENUMS - Definiciones de tipos enumerados
# =============================================================================


class RatingType(PyEnum):
    """
    Tipo de calificación según quién califica a quién.
    """

    PASSENGER_TO_DRIVER = "passenger_to_driver"
    DRIVER_TO_PASSENGER = "driver_to_passenger"


# =============================================================================
# MODELO: Rating - Calificación después de un viaje
# =============================================================================


class Rating(BaseModel, Base):
    """
    Calificación que un usuario da a otro después de un viaje.

    Cada Rating tiene un trip_id, rater_id (quien califica),
    rated_id (quien recibe la calificación), y un score de 1 a 5.
    Se aplica tanto a viajes de transporte como a entregas de paquetes.

    Restricción única: un usuario solo puede calificar una vez por viaje.
    Esto se implementa con UniqueConstraint en (trip_id, rater_id, rating_type).
    """

    __tablename__ = "ratings"

    __table_args__ = (
        UniqueConstraint(
            "trip_id",
            "rater_id",
            "rating_type",
            name="uq_rating_per_trip_user_type",
        ),
    )

    trip_id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trips.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="al qué viaje pertenece esta calificación",
    )

    rater_id: Mapped[uuid4 | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="quien da la calificación (nullable para conservar rating si el usuario es eliminado)",
    )

    rated_id: Mapped[uuid4 | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="quien recibe la calificación (nullable para conservar rating si el usuario es eliminado)",
    )

    rating_type: Mapped[RatingType] = mapped_column(
        Enum(RatingType),
        nullable=False,
    )

    score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="de 1 a 5 estrellas, validar en el schema",
    )

    comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="comentario opcional del usuario sobre la experiencia",
    )

    trip: Mapped["Trip"] = relationship(
        "Trip",
        back_populates="ratings",
        lazy="selectin",
    )

    rater: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[rater_id],
        lazy="selectin",
    )

    rated: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[rated_id],
        lazy="selectin",
    )

    @property
    def score_display(self) -> str:
        """
        Retorna el score con texto descriptivo.

        Returns:
            str: Score con estrellas y descripción

        Examples:
            score=5 → "5 ★ Excelente"
            score=3 → "3 ★ Regular"
            score=1 → "1 ★ Malo"
        """
        descriptions = {
            5: "Excelente",
            4: "Bueno",
            3: "Regular",
            2: "Malo",
            1: "Muy Malo",
        }
        desc = descriptions.get(self.score, "Sin descripción")
        return f"{self.score} ★ {desc}"


from app.models.trip import Trip
from app.models.user import User