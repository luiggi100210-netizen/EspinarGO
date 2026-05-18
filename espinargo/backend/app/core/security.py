"""
Módulo de operaciones criptográficas puras.

Este módulo contiene funciones que transforman datos de forma segura:
- Hash de contraseñas con bcrypt
- Creación y verificación de tokens JWT
- Generación de tokens aleatorios seguros
- Generación y verificación de códigos OTP

NO contiene lógica de negocio ni acceso a base de datos.
Es importado por auth_service.py y middleware/auth.py.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import jwt
from jwt.exceptions import PyJWTError as JWTError
from passlib.context import CryptContext

from app.core.config import settings


# =============================================================================
# CONTEXTO DE BCRYPT - Hash de contraseñas
# =============================================================================

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)

"""
CryptContext para hash de contraseñas.

bcrypt es un algoritmo de hash diseñado para ser lento y costoso
computacionalmente, lo que hace muy difícil los ataques de fuerza bruta.
A diferencia de MD5 o SHA:
- Incorpora un "salt" aleatorio automáticamente
- Permite configurar el "cost" (factor de trabajo) para ajustar seguridad
- Ha sido ampliamente auditado y es considerado seguro

El factor de costo por defecto de bcrypt (12) es un buen balance entre
seguridad y rendimiento para la mayoría de aplicaciones.
"""


# =============================================================================
# FUNCIONES DE CONTRASEÑA
# =============================================================================


def hash_password(plain_password: str) -> str:
    """
    Genera un hash bcrypt de la contraseña en texto plano.

    El hash incluye el salt automáticamente, por lo que cada vez
    que se llama con la misma contraseña, el resultado es diferente
    (pero todos son válidos para verificar).

    Args:
        plain_password: Contraseña en texto plano del usuario.

    Returns:
        str: Hash bcrypt listo para almacenar en la base de datos.

    Example:
        >>> hash = hash_password("mi_contraseña")
        >>> hash  # $2b$12$...
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed: str) -> bool:
    """
    Verifica si una contraseña coincide con su hash almacenado.

    Usa comparación en tiempo constante para evitar ataques de timing
    que podrían revelar información sobre la contraseña basándose
    en cuánto tiempo tarda la comparación.

    Args:
        plain_password: Contraseña en texto plano a verificar.
        hashed: Hash almacenado en la base de datos.

    Returns:
        bool: True si la contraseña coincide, False si no.

    Example:
        >>> stored_hash = hash_password("secreto")
        >>> verify_password("secreto", stored_hash)
        True
        >>> verify_password("incorrecto", stored_hash)
        False
    """
    return pwd_context.verify(plain_password, hashed)


# =============================================================================
# FUNCIONES JWT - Tokens de acceso
# =============================================================================


def create_access_token(
    user_id: UUID,
    role: str,
    phone_number: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Crea un JWT (JSON Web Token) para acceso autenticado.

    Un JWT tiene 3 partes separadas por puntos:
    1. Header: algoritmo y tipo de token
    2. Payload: datos del usuario (no sensibles)
    3. Signature: firma criptográfica que verifica autenticidad

    El access token dura solo 30 minutos por seguridad: si alguien
    roba un token, tiene acceso limitado en el tiempo.

    Incluimos el rol en el payload para evitar consultar la base de datos
    en cada request, lo cual mejora el rendimiento.

    Args:
        user_id: UUID del usuario autenticado.
        role: Rol del usuario ("passenger", "driver", "admin").
        phone_number: Número de teléfono del usuario.
        expires_delta: Tiempo adicional de expiración (opcional).

    Returns:
        str: Token JWT firmado listo para usar en Authorization header.

    Example:
        >>> token = create_access_token(
        ...     user_id=UUID("123e4567..."),
        ...     role="driver",
        ...     phone_number="+51987654321"
        ... )
        >>> # Usar en header: Authorization: Bearer <token>
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    payload = {
        "sub": str(user_id),
        "role": role,
        "phone": phone_number,
        "iat": datetime.now(timezone.utc),
        "exp": expire,
        "type": "access",
        "jti": secrets.token_hex(16),
    }

    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decodifica y valida un JWT de acceso.

    Verifica que el token sea válido, no haya expirado,
    y que sea específicamente un token de tipo "access"
    (para evitar usar refresh tokens donde se esperan access tokens).

    Args:
        token: Token JWT a decodificar.

    Returns:
        dict: Payload del token si es válido.

    Raises:
        JWTError: Si el token es inválido, expirado, o no es de tipo access.

    Example:
        >>> try:
        ...     payload = decode_access_token(token)
        ...     user_id = payload["sub"]
        ... except JWTError:
        ...     # Token inválido o expirado
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        if payload.get("type") != "access":
            raise JWTError("Token no es de tipo access")

        return payload

    except JWTError:
        raise


# =============================================================================
# REFRESH TOKEN - Tokens para mantener sesiones
# =============================================================================


def generate_refresh_token() -> str:
    """
    Genera un token aleatorio criptográficamente seguro para refresh.

    A diferencia de los JWT, este es un "token opaco": no contiene
    información en sí mismo, solo un identificador aleatorio que
    se verifica contra la base de datos. Esto es más seguro porque
    el token no puede ser modificado por el cliente.

    Se almacena en la tabla refresh_tokens y se verifica ahí.

    128 caracteres hexadecimales proporcionan 256 bits de entropía,
    suficiente para que sea prácticamente imposible de adivinar.

    Returns:
        str: Token aleatorio de 128 caracteres hexadecimales.

    Example:
        >>> token = generate_refresh_token()
        >>> len(token)
        128
    """
    return secrets.token_hex(64)


def get_refresh_token_expiry() -> datetime:
    """
    Calcula la fecha de expiración del refresh token.

    El refresh token dura 30 días por defecto, permitiendo al usuario
    mantener la sesión activa sin necesidad de iniciar sesión frecuentemente.

    Returns:
        datetime: Fecha y hora UTC de expiración.

    Example:
        >>> expiry = get_refresh_token_expiry()
        >>> # datetime(2024, 4, 20, 12, 0, 0, tzinfo=timezone.utc)
    """
    return datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)


# =============================================================================
# OTP - Códigos de verificación SMS
# =============================================================================


def generate_otp_code(length: int = 6) -> str:
    """
    Genera un código OTP numérico aleatorio.

    En modo DEVELOPMENT siempre retorna "123456" para facilitar
    pruebas sin consumir créditos de Twilio. En staging y production
    genera un código aleatorio real usando secrets para criptografía.

    Args:
        length: Longitud del código (por defecto 6 dígitos).

    Returns:
        str: Código OTP.

    Example:
        >>> # En development
        >>> generate_otp_code()
        '123456'

        >>> # En production
        >>> generate_otp_code()  # '472891'
    """
    if settings.is_development:
        return "123456"

    code = ""
    for _ in range(length):
        code += str(secrets.randbelow(10))
    return code


def get_otp_expiry() -> datetime:
    """
    Calcula la fecha de expiración del código OTP.

    El código expira en 10 minutos por defecto (configurable en settings).
    Esto balancea seguridad (tiempo limitado para usar el código)
    con usabilidad (tiempo suficiente para que el usuario lo recepte).

    Returns:
        datetime: Fecha y hora UTC de expiración del código.

    Example:
        >>> expiry = get_otp_expiry()
        >>> # datetime(2024, 4, 15, 12, 10, 0, tzinfo=timezone.utc)
    """
    return datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)


def hash_otp(code: str) -> str:
    """
    Genera un hash SHA-256 del código OTP para almacenamiento seguro.

    Los OTPs no se deben guardar en texto plano. SHA-256 es suficiente
    aquí (a diferencia de bcrypt para contraseñas) porque los OTPs
    expiran en minutos y tienen límite de intentos.

    Args:
        code: Código OTP en texto plano.

    Returns:
        str: Hash SHA-256 en hexadecimal (64 chars).
    """
    return hashlib.sha256(code.encode()).hexdigest()


def verify_otp_code(plain_code: str, hashed_code: str) -> bool:
    """
    Verifica un código OTP usando comparación en tiempo constante.

    Args:
        plain_code: Código introducido por el usuario.
        hashed_code: Hash almacenado en la base de datos.

    Returns:
        bool: True si el código es correcto.
    """
    return secrets.compare_digest(hash_otp(plain_code), hashed_code)


def mask_phone_number(phone: str) -> str:
    """
    Enmasca el número de teléfono para mostrar en la UI.

    Protege la privacidad del usuario mostrando solo los últimos
    dígitos del número. El formato es: +51 ****** XX

    Args:
        phone: Número de teléfono en formato +51XXXXXXXXX

    Returns:
        str: Número enmascarado seguro para mostrar.

    Example:
        >>> mask_phone_number("+51987654321")
        '+51 ****** 21'
    """
    if len(phone) < 4:
        return phone

    last_two = phone[-2:]
    return f"+51 ****** {last_two}"