"""
Schemas para el flujo de autenticación.

Incluye registro, verificación OTP, login, gestión de tokens
y recuperación de contraseña.
"""

from typing import Optional

from pydantic import Field, field_validator
from uuid import UUID

from app.schemas.base import (
    EspinarGoBaseModel,
    MessageResponse,
    validate_peru_phone,
    validate_password_strength,
)


class RegisterRequest(EspinarGoBaseModel):
    """
    Datos para crear una cuenta nueva.
    """

    full_name: str = Field(
        ...,
        min_length=2,
        max_length=150,
        description="Nombre completo del usuario",
        examples=["Juan Quispe Mamani"],
    )
    phone_number: str = Field(
        ...,
        description="Celular peruano con código de país",
        examples=["+51987654321"],
    )
    email: Optional[str] = Field(
        default=None,
        examples=["juan@gmail.com"],
        description="Correo electrónico opcional",
    )
    password: str = Field(
        ...,
        min_length=6,
        description="Contraseña mínimo 6 caracteres",
        examples=["miClave123"],
    )
    role: str = Field(
        default="passenger",
        description="Rol del usuario en la aplicación",
        examples=["passenger", "driver"],
    )

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return validate_peru_phone(v)

    @field_validator("password")
    @classmethod
    def validate_pwd(cls, v: str) -> str:
        return validate_password_strength(v)

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        valid_roles = ["passenger", "driver"]
        if v not in valid_roles:
            raise ValueError("El rol debe ser 'passenger' o 'driver'")
        return v

    @field_validator("full_name")
    @classmethod
    def normalize_name(cls, v: str) -> str:
        return v.strip().title()


class RegisterResponse(EspinarGoBaseModel):
    """
    Confirmación del registro exitoso.
    """

    message: str = Field(..., description="Mensaje informativo")
    user_id: UUID = Field(..., description="ID del usuario creado")
    phone_number: str = Field(..., description="Número registrado")
    next_step: str = Field(
        default="verify_phone",
        description="Guía al frontend al siguiente paso",
    )


class SendOTPRequest(EspinarGoBaseModel):
    """
    Solicitar envío de código SMS.
    """

    phone_number: str = Field(..., description="Número de teléfono")
    purpose: str = Field(
        default="phone_verify",
        description="Propósito del código: phone_verify, login, password_reset",
    )

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return validate_peru_phone(v)

    @field_validator("purpose")
    @classmethod
    def validate_purpose(cls, v: str) -> str:
        valid_purposes = ["phone_verify", "login", "password_reset"]
        if v not in valid_purposes:
            raise ValueError(
                f"El propósito debe ser uno de: {', '.join(valid_purposes)}"
            )
        return v


class SendOTPResponse(EspinarGoBaseModel):
    """
    Confirmación del envío del SMS.
    """

    message: str = Field(default="Código enviado por SMS")
    expires_in: int = Field(..., description="Segundos hasta que expira el código")
    masked_phone: str = Field(
        ...,
        description="Número enmascarado ej: +51 ****** 21",
    )


class VerifyOTPRequest(EspinarGoBaseModel):
    """
    Verificar el código recibido por SMS.
    """

    phone_number: str = Field(..., description="Número de teléfono")
    code: str = Field(
        ...,
        min_length=6,
        max_length=6,
        description="Código de 6 dígitos recibido por SMS",
    )
    purpose: str = Field(default="phone_verify")

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return validate_peru_phone(v)

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("El código debe contener solo números")
        return v


class VerifyOTPResponse(EspinarGoBaseModel):
    """
    Respuesta de verificación de OTP.
    """

    message: str = Field(..., description="Mensaje de resultado")
    verified: bool = Field(..., description="True si fue verificado correctamente")


class LoginRequest(EspinarGoBaseModel):
    """
    Credenciales para iniciar sesión.
    """

    phone_number: str = Field(..., description="Número de teléfono")
    password: str = Field(..., description="Contraseña")
    device_name: Optional[str] = Field(
        default=None,
        examples=["Samsung Galaxy A54"],
        description="Nombre del dispositivo para gestión de sesiones",
    )
    device_os: Optional[str] = Field(
        default=None,
        examples=["Android 14"],
    )
    device_token: Optional[str] = Field(
        default=None,
        description="Token FCM para recibir notificaciones push",
    )

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return validate_peru_phone(v)


class TokenResponse(EspinarGoBaseModel):
    """
    Tokens retornados tras login exitoso.
    """

    access_token: str = Field(..., description="JWT válido por 30 minutos")
    refresh_token: str = Field(..., description="Token opaco válido por 30 días")
    token_type: str = Field(default="bearer")
    expires_in: int = Field(..., description="Segundos hasta expiración del access token")
    user: "UserPublicOut" = Field(..., description="Datos básicos del usuario")


class RefreshTokenRequest(EspinarGoBaseModel):
    """
    Solicitar nuevo access token.
    """

    refresh_token: str = Field(..., description="El refresh token almacenado en el dispositivo")


class RefreshTokenResponse(EspinarGoBaseModel):
    """
    Respuesta con nuevo access token.
    """

    access_token: str = Field(..., description="Nuevo JWT válido por 30 minutos")
    token_type: str = Field(default="bearer")
    expires_in: int = Field(..., description="Segundos hasta expiración")


class ChangePasswordRequest(EspinarGoBaseModel):
    """
    Cambiar contraseña (usuario autenticado).
    """

    current_password: str = Field(..., description="Contraseña actual")
    new_password: str = Field(..., description="Nueva contraseña")

    @field_validator("new_password")
    @classmethod
    def validate_pwd(cls, v: str) -> str:
        return validate_password_strength(v)


class ResetPasswordRequest(EspinarGoBaseModel):
    """
    Restablecer contraseña con código OTP.
    """

    phone_number: str = Field(..., description="Número de teléfono")
    otp_code: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., description="Nueva contraseña")

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return validate_peru_phone(v)

    @field_validator("otp_code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("El código debe contener solo números")
        return v

    @field_validator("new_password")
    @classmethod
    def validate_pwd(cls, v: str) -> str:
        return validate_password_strength(v)


from app.schemas.user import UserPublicOut