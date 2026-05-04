"""
Modelos para el servicio de encomiendas/envíos.

Contiene 2 modelos principales:
- Package: información del envío
- PackageTracking: historial de estados del paquete

El servicio de encomiendas permite a los usuarios enviar paquetes
dentro de Espinar y zonas cercanas, con tracking en tiempo real.
"""

from datetime import datetime
from enum import Enum as PyEnum
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base_model import BaseModel


# =============================================================================
# ENUMS - Definiciones de tipos enumerados
# =============================================================================


class PackageSize(PyEnum):
    """
    Tamaño del paquete según dimensiones.
    """

    ENVELOPE = "envelope"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class PackageStatus(PyEnum):
    """
    Estado del paquete a lo largo del envío.
    """

    PENDING = "pending"
    ASSIGNED = "assigned"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


# =============================================================================
# MODELO: Package - Envío/encomienda
# =============================================================================


class Package(BaseModel, Base):
    """
    Paquete/encomienda que se envía de un punto a otro.

    El flujo typical es:
    1. PENDING: el remitente creó la orden, esperando conductor
    2. ASSIGNED: un conductor tomó el envío
    3. PICKED_UP: el conductor recogió el paquete
    4. IN_TRANSIT: el conductor va hacia el destino
    5. DELIVERED: el paquete llegó al destinatario
    6. CANCELLED: el envío se canceló
    """

    __tablename__ = "packages"

    sender_id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
        index=True,
        doc="quien envía el paquete",
    )

    driver_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="conductor asignado, null hasta que un conductor acepte el envío",
    )

    tracking_code: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
        index=True,
        doc="código único formato ESP-YYYYMMDD-NNNN, ejemplo: ESP-20240420-0042",
    )

    recipient_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        doc="nombre de la persona que recibe el paquete",
    )

    recipient_phone: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="se notifica por SMS cuando el paquete llega",
    )

    delivery_address: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
        doc="dirección de entrega del paquete",
    )

    delivery_lat: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    delivery_lng: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    size: Mapped[PackageSize] = mapped_column(
        Enum(PackageSize),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="contenido del paquete declarado por el remitente",
    )

    is_fragile: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="indica manejo especial al conductor",
    )

    photo_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="foto del paquete antes de enviarlo",
    )

    price: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        doc="precio en soles calculado según tamaño y distancia",
    )

    payment_method: Mapped[str] = mapped_column(
        String(20),
        default="cash",
        nullable=False,
    )

    status: Mapped[PackageStatus] = mapped_column(
        Enum(PackageStatus),
        default=PackageStatus.PENDING,
        nullable=False,
        index=True,
    )

    picked_up_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="cuando el conductor recogió el paquete",
    )

    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="cuando el paquete fue entregado al destinatario",
    )

    sender: Mapped["User"] = relationship(
        "User",
        foreign_keys=[sender_id],
        lazy="selectin",
    )

    driver: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[driver_id],
        lazy="selectin",
    )

    tracking_history: Mapped[list["PackageTracking"]] = relationship(
        "PackageTracking",
        back_populates="package",
        cascade="all, delete-orphan",
        order_by="PackageTracking.created_at",
        lazy="selectin",
    )

    @property
    def is_active(self) -> bool:
        """Retorna True si el paquete está en curso."""
        return self.status not in (PackageStatus.DELIVERED, PackageStatus.CANCELLED)


# =============================================================================
# MODELO: PackageTracking - Historial de estados del paquete
# =============================================================================


class PackageTracking(BaseModel, Base):
    """
    Registro de cada cambio de estado del paquete.

    Cada fila representa un evento en el historial del paquete.
    Se muestra como una línea de tiempo (timeline) en la app del usuario.
    Ejemplo: "Conductor Carlos D. recogió tu paquete"
    """

    __tablename__ = "package_tracking"

    package_id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("packages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="paquete al que pertenece este evento",
    )

    status: Mapped[PackageStatus] = mapped_column(
        Enum(PackageStatus),
        nullable=False,
        doc="nuevo estado del paquete en este evento",
    )

    description: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
        doc="mensaje legible del evento, ej: Conductor Carlos D. recogió tu paquete",
    )

    location_lat: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    location_lng: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    updated_by: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        doc="ID del usuario que generó el evento (conductor o sistema)",
    )

    package: Mapped["Package"] = relationship(
        "Package",
        back_populates="tracking_history",
        lazy="selectin",
    )


from app.models.user import User