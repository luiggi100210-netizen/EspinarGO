"""
Servicio de códigos OTP y envío de SMS.

Maneja todo el ciclo de vida de los códigos de verificación:
- Generación de códigos aleatorios seguros
- Rate limiting en Redis para evitar abuso
- Envío de SMS vía Twilio
- Verificación de códigos

Este servicio es la única parte del sistema que habla con Twilio.
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Optional

import redis.asyncio as aioredis
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client as TwilioClient

from app.core.config import settings
from app.core.security import generate_otp_code, get_otp_expiry, mask_phone_number
from app.models.user import OTPCode, User


# =============================================================================
# CLIENTE REDIS - Singleton para rate limiting
# =============================================================================

_redis_client: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    """
    Retorna el cliente de Redis (patrón singleton).

    El patrón singleton evita crear múltiples conexiones a Redis
    en cada llamada, lo cual podría agotar el pool de conexiones.

    Returns:
        aioredis.Redis: Cliente de Redis configurado.

    Example:
        >>> redis = await get_redis()
        >>> await redis.get("mi_clave")
    """
    global _redis_client

    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )

    return _redis_client


# =============================================================================
# CLIENTE TWILIO - Singleton para SMS
# =============================================================================

_twilio_client: Optional[TwilioClient] = None


def get_twilio_client() -> TwilioClient:
    """
    Retorna el cliente de Twilio (patrón singleton).

    Twilio no tiene una API async, por eso usamos el cliente sincrónico.
    El patrón singleton evita crear múltiples clientes.

    Returns:
        TwilioClient: Cliente de Twilio configurado.

    Example:
        >>> client = get_twilio_client()
        >>> client.messages.create(body="...", from_="...", to="...")
    """
    global _twilio_client

    if _twilio_client is None:
        _twilio_client = TwilioClient(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN,
        )

    return _twilio_client


# =============================================================================
# RATE LIMITING - Evitar abuso de OTP
# =============================================================================


async def check_otp_rate_limit(phone_number: str) -> tuple[bool, int]:
    """
    Verifica si el usuario puede solicitar un nuevo código OTP.

    Limita la cantidad de códigos que un usuario puede solicitar
    por hora para evitar abuso (spam de SMS, costos excesivos).
    Usa Redis con pipeline para operación atómica.

    Args:
        phone_number: Número de teléfono del usuario.

    Returns:
        tuple: (permitido: bool, segundos_de_espera: int)
               Si permitido es True, segundos será 0.
               Si permitido es False, segundos es el tiempo a esperar.

    Example:
        >>> allowed, wait_seconds = await check_otp_rate_limit("+51987654321")
        >>> if not allowed:
        ...     print(f"Espera {wait_seconds} segundos")
    """
    redis = await get_redis()
    key = f"otp_rate:{phone_number}"

    current_count = await redis.get(key)

    if current_count and int(current_count) >= settings.OTP_RATE_LIMIT_PER_HOUR:
        ttl = await redis.ttl(key)
        return False, max(ttl, 0)

    pipe = redis.pipeline()
    pipe.incr(key)
    pipe.expire(key, 3600)
    await pipe.execute()

    return True, 0


# =============================================================================
# SERVICIO OTP - Clase principal
# =============================================================================


class OTPService:
    """
    Servicio para gestionar códigos OTP de verificación.

    Maneja el ciclo completo: enviar códigos por SMS,
    verificar que sean válidos, y controlar el rate limiting.
    """

    @staticmethod
    async def send_otp(
        db: AsyncSession,
        user: User,
        purpose: str = "phone_verify",
    ) -> dict:
        """
        Envía un código OTP al número de teléfono del usuario.

        El proceso incluye:
        1. Verificar rate limiting
        2. Invalidar códigos anteriores del mismo propósito
        3. Generar nuevo código
        4. Crear registro en la base de datos
        5. Enviar SMS

        Args:
            db: Sesión de base de datos.
            user: Usuario que recibe el código.
            purpose: Propósito del código (phone_verify, login, password_reset).

        Returns:
            dict: Mensaje, tiempo de expiración en segundos, teléfono enmascarado.

        Raises:
            ValueError: Si se excede el rate limit o falla el envío.

        Example:
            >>> result = await OTPService.send_otp(db, user, "phone_verify")
            >>> print(result["masked_phone"])
            '+51 ****** 21'
        """
        allowed, wait_seconds = await check_otp_rate_limit(user.phone_number)

        if not allowed:
            minutes_to_wait = (wait_seconds // 60) + 1
            raise ValueError(
                f"Has solicitado muchos códigos. "
                f"Intenta de nuevo en {minutes_to_wait} minuto(s)."
            )

        await db.execute(
            update(OTPCode)
            .where(
                OTPCode.user_id == user.id,
                OTPCode.purpose == purpose,
                OTPCode.is_used == False,
            )
            .values(is_used=True)
        )

        code = generate_otp_code()
        expires_at = get_otp_expiry()

        otp = OTPCode(
            user_id=user.id,
            code=code,
            purpose=purpose,
            expires_at=expires_at,
        )
        db.add(otp)
        await db.flush()

        message = OTPService._build_sms_message(code, purpose)

        await OTPService._send_sms(user.phone_number, message)

        expires_in = int((expires_at - datetime.now(timezone.utc)).total_seconds())

        return {
            "message": "Código enviado por SMS",
            "expires_in": expires_in,
            "masked_phone": mask_phone_number(user.phone_number),
        }

    @staticmethod
    async def verify_otp(
        db: AsyncSession,
        user: User,
        code: str,
        purpose: str = "phone_verify",
    ) -> bool:
        """
        Verifica que el código OTP sea válido.

        El proceso incluye:
        1. Buscar el código activo más reciente
        2. Verificar que no haya expirado
        3. Verificar que no supere el máximo de intentos
        4. Comparar el código (incrementa intentos si falla)
        5. Marcar como usado si es válido

        Args:
            db: Sesión de base de datos.
            user: Usuario que introdujo el código.
            code: Código de 6 dígitos a verificar.
            purpose: Propósito del código (phone_verify, login, password_reset).

        Returns:
            bool: True si el código es válido.

        Raises:
            ValueError: Si el código es inválido, expirado, o excede intentos.
        """
        now = datetime.now(timezone.utc)

        result = await db.execute(
            select(OTPCode)
            .where(
                OTPCode.user_id == user.id,
                OTPCode.purpose == purpose,
                OTPCode.is_used == False,
            )
            .order_by(OTPCode.created_at.desc())
            .limit(1)
        )
        otp = result.scalar_one_or_none()

        if not otp:
            raise ValueError("No hay código activo. Solicita uno nuevo.")

        if otp.expires_at.astimezone(timezone.utc) < now:
            raise ValueError("El código expiró. Solicita uno nuevo.")

        if otp.attempts >= settings.OTP_MAX_ATTEMPTS:
            raise ValueError(
                f"Has intentado muchas veces. Solicita un código nuevo."
            )

        if otp.code != code:
            otp.attempts += 1
            remaining = settings.OTP_MAX_ATTEMPTS - otp.attempts
            raise ValueError(
                f"Código incorrecto. Te quedan {remaining} intento(s)."
            )

        otp.is_used = True
        otp.verified_at = now

        return True

    @staticmethod
    def _build_sms_message(code: str, purpose: str) -> str:
        """
        Construye el mensaje SMS según el propósito.

        Args:
            code: Código OTP de 6 dígitos.
            purpose: Propósito del código.

        Returns:
            str: Mensaje SMS formateado.
        """
        validity = settings.OTP_EXPIRE_MINUTES

        if purpose == "phone_verify":
            return (
                "🛵 EspinarGo: Tu código de verificación es "
                f"{code}. Válido por {validity} minutos. "
                "No compartas este código."
            )

        elif purpose == "login":
            return (
                "🛵 EspinarGo: Tu código de acceso es "
                f"{code}. Válido por {validity} minutos."
            )

        elif purpose == "password_reset":
            return (
                "🛵 EspinarGo: Tu código de recuperación es "
                f"{code}. Válido por {validity} minutos. "
                "Si no lo solicitaste, ignora este mensaje."
            )

        return f"EspinarGo: Tu código es {code}"

    @staticmethod
    async def _send_sms(phone_number: str, message: str) -> None:
        """
        Envía el SMS al número especificado.

        En modo development no envía SMS reales, solo los muestra
        en consola para evitar consumir créditos de Twilio.

        Args:
            phone_number: Número de teléfono destino.
            message: Mensaje a enviar.

        Raises:
            ValueError: Si falla el envío en producción.
        """
        if settings.is_development:
            print("=" * 50)
            print(f"SMS DEBUG → {phone_number}")
            print("=" * 50)
            print(message)
            print("=" * 50)
            return

        try:
            client = get_twilio_client()
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None,
                lambda: client.messages.create(
                    body=message,
                    from_=settings.TWILIO_PHONE_NUMBER,
                    to=phone_number,
                ),
            )
        except TwilioRestException as e:
            print(f"Error de Twilio: {e}")
            raise ValueError(
                "No se pudo enviar el SMS. Verifica tu número e intenta de nuevo."
            )