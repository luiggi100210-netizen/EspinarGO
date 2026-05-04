"""
Modelos relacionados con usuarios del sistema.

Contiene 4 modelos principales:
- User: usuario principal de la aplicación
- RefreshToken: tokens para mantener sesiones activas
- OTPCode: códigos de verificación SMS
- DriverProfile: perfil específico para conductores

También define los Enum usados en estos modelos:
- UserRole: rol del usuario (pasajero, conductor, admin)
- UserStatus: estado de verificación del usuario
- DriverStatus: estado del proceso de aprobación del conductor
- VehicleType: tipo de vehículo del conductor
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


class UserRole(PyEnum):
    """
    Rol del usuario en el sistema.

    Determina qué acciones puede realizar el usuario en la aplicación.
    """

    PASSENGER = "passenger"
    DRIVER = "driver"
    ADMIN = "admin"


class UserStatus(PyEnum):
    """
    Estado de verificación del usuario.

    El usuario comienza en PENDING hasta verificar su teléfono,
    luego pasa a ACTIVE. Los administradores pueden suspender o banear.
    """

    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    BANNED = "banned"


class DriverStatus(PyEnum):
    """
    Estado del proceso de aprobación del conductor.

    El conductor debe subir documentos, luego el admin los revisa.
    Solo puede trabajar cuando está APPROVED.
    """

    PENDING_DOCS = "pending_docs"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class VehicleType(PyEnum):
    """
    Tipo de vehículo del conductor.
    """

    MOTOTAXI = "mototaxi"
    CAR = "car"


# =============================================================================
# MODELO: User - Usuario principal del sistema
# =============================================================================


class User(BaseModel, Base):
    """
    Usuario principal de la aplicación EspinarGo.

    Representa tanto pasajeros como conductores. El campo role determina
    qué puede hacer el usuario. Un usuario puede ser ambos (pasajero y conductor)
    si tiene un DriverProfile asociado.
    """

    __tablename__ = "users"

    full_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        doc="nombre completo del usuario",
    )

    phone_number: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
        doc="número peruano formato +51XXXXXXXXX, es el identificador principal de login",
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
        doc="opcional, alternativa de contacto",
    )

    password_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="hash bcrypt, null si el usuario entró con OAuth",
    )

    phone_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="True solo después de verificar con OTP SMS",
    )

    email_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),
        default=UserRole.PASSENGER,
        nullable=False,
        doc="determina qué puede hacer en la app",
    )

    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus),
        default=UserStatus.PENDING,
        nullable=False,
        doc="PENDING hasta verificar teléfono, luego ACTIVE",
    )

    avatar_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="URL de Cloudinary con la foto de perfil",
    )

    google_id: Mapped[str | None] = mapped_column(
        String(100),
        unique=True,
        nullable=True,
        doc="ID de Google para OAuth, null si no usó login con Google",
    )

    facebook_id: Mapped[str | None] = mapped_column(
        String(100),
        unique=True,
        nullable=True,
        doc="ID de Facebook para OAuth, null si no usó login con Facebook",
    )

    device_token: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="token FCM para enviar push notifications",
    )

    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="última vez que el usuario abrió la app",
    )

    preferred_lang: Mapped[str] = mapped_column(
        String(5),
        default="es",
        nullable=False,
    )

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    otp_codes: Mapped[list["OTPCode"]] = relationship(
        "OTPCode",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    driver_profile: Mapped["DriverProfile | None"] = relationship(
        "DriverProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def is_active(self) -> bool:
        """Retorna True si el usuario está activo."""
        return self.status == UserStatus.ACTIVE

    @property
    def is_driver(self) -> bool:
        """Retorna True si el usuario es conductor."""
        return self.role == UserRole.DRIVER

    @property
    def is_passenger(self) -> bool:
        """Retorna True si el usuario es pasajero."""
        return self.role == UserRole.PASSENGER

    @property
    def is_admin(self) -> bool:
        """Retorna True si el usuario es administrador."""
        return self.role == UserRole.ADMIN

    @property
    def display_name(self) -> str:
        """Retorna el nombre completo capitalizado."""
        return self.full_name.title()

    def __repr__(self) -> str:
        return f"<User phone={self.phone_number} role={self.role.value}>"


# =============================================================================
# MODELO: RefreshToken - Token para mantener sesiones activas
# =============================================================================


class RefreshToken(BaseModel, Base):
    """
    Token para mantener la sesión del usuario activa.

    A diferencia de los JWT access tokens (que duran 30 minutos),
    los refresh tokens duran 30 días. Cuando el access token expira,
    el cliente usa el refresh token para obtener uno nuevo sin
    volver a pedir credenciales.
    """

    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="usuario al que pertenece este token de sesión",
    )

    token: Mapped[str] = mapped_column(
        String(500),
        unique=True,
        nullable=False,
        index=True,
        doc="token opaco de 128 chars hex, NO es JWT",
    )

    is_revoked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="True cuando el usuario cierra sesión",
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="fecha y hora en que el token deja de ser válido",
    )

    device_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="nombre del dispositivo, ej: Samsung Galaxy A54",
    )

    device_os: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="sistema operativo del dispositivo, ej: Android 14",
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
        doc="IPv4 o IPv6 del dispositivo, 45 chars soporta ambos",
    )

    user_agent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="cadena User-Agent del navegador o app",
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="refresh_tokens",
        lazy="selectin",
    )

    @property
    def is_expired(self) -> bool:
        """Retorna True si el token ya expiró."""
        return datetime.now(self.expires_at.tzinfo) > self.expires_at


# =============================================================================
# MODELO: OTPCode - Código de verificación por SMS
# =============================================================================


class OTPCode(BaseModel, Base):
    """
    Código de verificación de 6 dígitos enviado por SMS.

    Se usa para verificar el número de teléfono del usuario (registro),
    para login sin contraseña, y para recuperar contraseña.
    """

    __tablename__ = "otp_codes"

    user_id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="usuario al que pertenece este código",
    )

    code: Mapped[str] = mapped_column(
        String(6),
        nullable=False,
        doc="6 dígitos numéricos, ej: 472918",
    )

    purpose: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="phone_verify (verificar teléfono) | login (autenticación) | password_reset (recuperar contraseña)",
    )

    is_used: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="True cuando ya fue verificado o expiró",
    )

    attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="intentos fallidos, máximo 3 antes de invalidar",
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="fecha y hora límite para usar el código",
    )

    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="momento exacto en que se verificó correctamente",
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="otp_codes",
        lazy="selectin",
    )


# =============================================================================
# MODELO: DriverProfile - Perfil específico de conductor
# =============================================================================


class DriverProfile(BaseModel, Base):
    """
    Perfil específico para usuarios que son conductores.

    Contiene información del vehículo, documentos requeridos,
    estado de aprobación y estadísticas del conductor.
    """

    __tablename__ = "driver_profiles"

    user_id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
        doc="único porque un usuario tiene máximo 1 perfil conductor",
    )

    vehicle_type: Mapped[VehicleType | None] = mapped_column(
        Enum(VehicleType),
        nullable=True,
        doc="tipo de vehículo: mototaxi o auto",
    )

    vehicle_brand: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="marca del vehículo, ej: Bajaj",
    )

    vehicle_model: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="modelo del vehículo, ej: RE 205",
    )

    vehicle_year: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="año de fabricación del vehículo",
    )

    vehicle_color: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="color del vehículo",
    )

    vehicle_plate: Mapped[str | None] = mapped_column(
        String(20),
        unique=True,
        nullable=True,
        doc="placa del vehículo, ej: T3G-847",
    )

    vehicle_seats: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=True,
        doc="número de asientos disponibles para pasajeros",
    )

    vehicle_photo_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="URL de foto del vehículo",
    )

    dni_front_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="foto frontal del DNI",
    )

    dni_back_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="foto posterior del DNI",
    )

    license_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="foto del brevete categoría A-I",
    )

    soat_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="foto del SOAT vigente",
    )

    property_card_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="tarjeta de propiedad del vehículo",
    )

    selfie_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="selfie para verificación de identidad",
    )

    driver_status: Mapped[DriverStatus] = mapped_column(
        Enum(DriverStatus),
        default=DriverStatus.PENDING_DOCS,
        nullable=False,
        doc="estado del proceso de aprobación",
    )

    rejection_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="razón del rechazo que se muestra al conductor",
    )

    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="fecha en que el conductor fue aprobado",
    )

    approved_by: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        doc="ID del admin que aprobó al conductor",
    )

    total_trips: Mapped[int] = mapped_column(
        Integer,
        default=0,
        doc="número total de viajes completados",
    )

    rating: Mapped[int] = mapped_column(
        Integer,
        default=50,
        doc="escala interna 0-50, se muestra como 0.0-5.0. Ejemplo: 48 interno = 4.8 estrellas mostradas",
    )

    rating_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        doc="número de calificaciones recibidas",
    )

    is_online: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        doc="True cuando el conductor está buscando viajes",
    )

    current_lat: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        doc="latitud actual del conductor",
    )

    current_lng: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        doc="longitud actual del conductor, se actualiza cada 5 segundos vía WebSocket",
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="driver_profile",
        lazy="selectin",
    )

    @property
    def rating_display(self) -> str:
        """Convierte el rating interno a estrellas."""
        return round(self.rating / 10, 1)

    @property
    def is_approved(self) -> bool:
        """Retorna True si el conductor está aprobado."""
        return self.driver_status == DriverStatus.APPROVED