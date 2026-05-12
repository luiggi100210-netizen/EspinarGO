"""
Servicio de autenticación y gestión de sesiones.

Contiene toda la lógica de negocio del ciclo de autenticación:
registro de usuarios, verificación de teléfono, login, manejo
de tokens JWT y refresh tokens, y reset de contraseña.

Este es el único lugar donde se toman decisiones de negocio
sobre autenticación. Los endpoints solo llaman a este servicio.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    get_refresh_token_expiry,
    hash_password,
    verify_password,
)
from app.models.user import DriverProfile, RefreshToken, User, UserRole, UserStatus
from app.services.otp_service import OTPService


# =============================================================================
# SERVICIO DE AUTENTICACIÓN
# =============================================================================


class AuthService:
    """
    Servicio central de autenticación de EspinarGo.

    Maneja todas las operaciones relacionadas con:
    - Registro de nuevos usuarios
    - Verificación de número de teléfono
    - Login y logout
    - Renovación de tokens
    - Recuperación de contraseña
    """

    @staticmethod
    async def register(db: AsyncSession, data) -> User:
        """
        Registra un nuevo usuario en el sistema.

        El proceso incluye:
        1. Verificar que el teléfono no esté registrado
        2. Verificar que el email no esté en uso (si se proporciona)
        3. Crear el usuario con estado PENDING (pendiente de verificación)
        4. Crear perfil de conductor si el rol es driver
        5. Enviar código OTP de verificación

        Args:
            db: Sesión de base de datos.
            data: Objeto con full_name, phone_number, email, password, role.

        Returns:
            User: Usuario recién creado.

        Raises:
            ValueError: Si el teléfono o email ya están registrados.

        Example:
            >>> class RegisterData:
            ...     full_name = "Juan Pérez"
            ...     phone_number = "+51987654321"
            ...     email = "juan@email.com"
            ...     password = "secreto123"
            ...     role = "passenger"
            >>>
            >>> user = await AuthService.register(db, RegisterData())
        """
        existing_user = await AuthService._get_user_by_phone(db, data.phone_number)
        if existing_user:
            raise ValueError(
                "Este número de teléfono ya está registrado. "
                "¿Querías iniciar sesión?"
            )

        if data.email:
            result = await db.execute(
                select(User).where(User.email == data.email)
            )
            if result.scalar_one_or_none():
                raise ValueError("El correo electrónico ya está en uso.")

        user = User(
            full_name=data.full_name.title(),
            phone_number=data.phone_number,
            email=getattr(data, "email", None),
            password_hash=hash_password(data.password),
            role=UserRole(data.role) if hasattr(data, "role") else UserRole.PASSENGER,
            status=UserStatus.PENDING,
        )
        db.add(user)
        await db.flush()

        if user.role == UserRole.DRIVER:
            driver_profile = DriverProfile(user_id=user.id)
            db.add(driver_profile)

        await OTPService.send_otp(db, user, "phone_verify")

        return user

    @staticmethod
    async def verify_phone(db: AsyncSession, phone_number: str, otp_code: str) -> dict:
        """
        Verifica el número de teléfono del usuario con el código OTP.

        Args:
            db: Sesión de base de datos.
            phone_number: Número de teléfono del usuario.
            otp_code: Código de 6 dígitos recibido por SMS.

        Returns:
            dict: Mensaje de éxito.

        Raises:
            ValueError: Si el código es inválido o el usuario no existe.

        Example:
            >>> result = await AuthService.verify_phone(
            ...     db, "+51987654321", "123456"
            ... )
            >>> print(result["message"])
            ¡Bienvenido a EspinarGo! Tu número ha sido verificado.
        """
        user = await AuthService._get_user_by_phone(db, phone_number)
        if not user:
            raise ValueError("Usuario no encontrado.")

        await OTPService.verify_otp(db, user, otp_code, "phone_verify")

        user.phone_verified = True
        user.status = UserStatus.ACTIVE

        return {
            "message": "¡Bienvenido a EspinarGo! Tu número ha sido verificado."
        }

    @staticmethod
    async def login(
        db: AsyncSession,
        data,
        ip_address: Optional[str] = None,
    ) -> dict:
        """
        Autentica al usuario y genera tokens de acceso.

        El proceso incluye:
        1. Buscar usuario por teléfono
        2. Verificar contraseña
        3. Verificar estado de la cuenta
        4. Verificar teléfono verificado
        5. Actualizar última sesión
        6. Generar access y refresh tokens
        7. Guardar refresh token en la base de datos

        Args:
            db: Sesión de base de datos.
            data: Objeto con phone_number, password, y opcionales.
            ip_address: IP del cliente (para logging).

        Returns:
            dict: access_token, refresh_token, token_type, expires_in, user.

        Raises:
            ValueError: Si las credenciales son incorrectas o la cuenta está inactiva.

        Example:
            >>> class LoginData:
            ...     phone_number = "+51987654321"
            ...     password = "secreto123"
            ...     device_name = "Samsung Galaxy"
            >>>
            >>> result = await AuthService.login(db, LoginData())
            >>> token = result["access_token"]
        """
        user = await AuthService._get_user_by_phone(db, data.phone_number)
        if not user:
            raise ValueError("Teléfono o contraseña incorrectos.")

        if not verify_password(data.password, user.password_hash or ""):
            raise ValueError("Teléfono o contraseña incorrectos.")

        if user.status == UserStatus.SUSPENDED:
            raise ValueError(
                "Tu cuenta está suspendida. Contacta a soporte para más información."
            )

        if user.status == UserStatus.BANNED:
            raise ValueError(
                "Tu cuenta ha sido bloqueada. Contacta a soporte para más información."
            )

        if not user.phone_verified:
            raise ValueError(
                "Debes verificar tu número de teléfono. "
                "Revisa el SMS que te enviamos."
            )

        user.last_seen_at = datetime.now(timezone.utc)

        if hasattr(data, "device_token") and data.device_token:
            user.device_token = data.device_token

        access_token = create_access_token(
            user_id=user.id,
            role=user.role.value,
            phone_number=user.phone_number,
        )

        refresh_token_str = generate_refresh_token()
        refresh_record = RefreshToken(
            user_id=user.id,
            token=refresh_token_str,
            expires_at=get_refresh_token_expiry(),
            device_name=getattr(data, "device_name", None),
            device_os=getattr(data, "device_os", None),
            ip_address=ip_address,
        )
        db.add(refresh_record)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token_str,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": user,
        }

    @staticmethod
    async def refresh_access_token(
        db: AsyncSession,
        refresh_token: str,
    ) -> dict:
        """
        Renueva el access token usando un refresh token válido.

        Args:
            db: Sesión de base de datos.
            refresh_token: Token de refresco almacenado en el cliente.

        Returns:
            dict: nuevo access_token, token_type, expires_in.

        Raises:
            ValueError: Si el token es inválido, expirado, o el usuario no existe.
        """
        now = datetime.now(timezone.utc)

        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.token == refresh_token,
                RefreshToken.is_revoked == False,
            )
        )
        token_record = result.scalar_one_or_none()

        if not token_record:
            raise ValueError("Token de refresco inválido.")

        expires_at = token_record.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < now:
            token_record.is_revoked = True
            raise ValueError(
                "Token de refresco expirado. Inicia sesión de nuevo."
            )

        user = await db.get(User, token_record.user_id)
        if not user or user.status != UserStatus.ACTIVE:
            raise ValueError("Usuario no válido o inactivo.")

        # Rotación de token: revocar el actual y emitir uno nuevo
        token_record.is_revoked = True
        new_refresh_token_str = generate_refresh_token()
        db.add(RefreshToken(
            user_id=user.id,
            token=new_refresh_token_str,
            expires_at=get_refresh_token_expiry(),
            device_name=token_record.device_name,
            device_os=token_record.device_os,
            ip_address=token_record.ip_address,
        ))

        new_access_token = create_access_token(
            user_id=user.id,
            role=user.role.value,
            phone_number=user.phone_number,
        )

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token_str,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    @staticmethod
    async def logout(db: AsyncSession, refresh_token: str) -> None:
        """
        Cierra la sesión actual revocando el refresh token.

        Es idempotente: si el token no existe o ya fue revocado,
        no lanza error.

        Args:
            db: Sesión de base de datos.
            refresh_token: Token de refresco a revocar.
        """
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.token == refresh_token)
        )
        token_record = result.scalar_one_or_none()

        if token_record:
            token_record.is_revoked = True

    @staticmethod
    async def logout_all_devices(db: AsyncSession, user_id: UUID) -> None:
        """
        Cierra todas las sesiones del usuario en todos los dispositivos.

        Más eficiente que revoked tokens uno por uno: usa una sola
        query de SQLAlchemy para actualizar todos los registros.

        Args:
            db: Sesión de base de datos.
            user_id: ID del usuario.
        """
        await db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked == False,
            )
            .values(is_revoked=True)
        )

    @staticmethod
    async def request_password_reset(
        db: AsyncSession,
        phone_number: str,
    ) -> dict:
        """
        Solicita un código OTP para recuperar la contraseña.

        Siempre retorna el mismo mensaje genérico sin revelar si el
        número existe en el sistema (seguridad contra enumeración).

        Args:
            db: Sesión de base de datos.
            phone_number: Número de teléfono del usuario.

        Returns:
            dict: Mensaje informativo.

        Example:
            >>> result = await AuthService.request_password_reset(
            ...     db, "+51987654321"
            ... )
            >>> print(result["message"])
            Si el número está registrado, recibirás un código SMS en breve.
        """
        user = await AuthService._get_user_by_phone(db, phone_number)

        if user and user.status == UserStatus.ACTIVE:
            await OTPService.send_otp(db, user, "password_reset")

        return {
            "message": (
                "Si el número está registrado, "
                "recibirás un código SMS en breve."
            )
        }

    @staticmethod
    async def reset_password(
        db: AsyncSession,
        phone_number: str,
        otp_code: str,
        new_password: str,
    ) -> dict:
        """
        Restablece la contraseña del usuario después de verificar el OTP.

        Args:
            db: Sesión de base de datos.
            phone_number: Número de teléfono del usuario.
            otp_code: Código OTP de recuperación.
            new_password: Nueva contraseña en texto plano.

        Returns:
            dict: Mensaje de éxito.

        Raises:
            ValueError: Si el código es inválido o el usuario no existe.
        """
        user = await AuthService._get_user_by_phone(db, phone_number)
        if not user:
            raise ValueError("Usuario no encontrado.")

        await OTPService.verify_otp(db, user, otp_code, "password_reset")

        user.password_hash = hash_password(new_password)

        await AuthService.logout_all_devices(db, user.id)

        return {
            "message": "Tu contraseña ha sido restablecida. "
            "Por favor, inicia sesión con tu nueva contraseña."
        }

    @staticmethod
    async def get_sessions(db: AsyncSession, user_id: UUID) -> list[RefreshToken]:
        """Retorna las sesiones activas (no revocadas y no expiradas) del usuario."""
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked == False,
                RefreshToken.expires_at > now,
            )
            .order_by(RefreshToken.created_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def revoke_session(
        db: AsyncSession, session_id: UUID, user_id: UUID
    ) -> None:
        """Revoca una sesión específica del usuario."""
        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.id == session_id,
                RefreshToken.user_id == user_id,
            )
        )
        token_record = result.scalar_one_or_none()
        if not token_record:
            raise LookupError("Sesión no encontrada")
        token_record.is_revoked = True

    @staticmethod
    async def _get_user_by_phone(
        db: AsyncSession,
        phone_number: str,
    ) -> Optional[User]:
        """
        Busca un usuario por su número de teléfono.

        Método privado para evitar duplicar esta query en varios métodos.

        Args:
            db: Sesión de base de datos.
            phone_number: Número de teléfono a buscar.

        Returns:
            Optional[User]: Usuario encontrado o None.

        Example:
            >>> user = await AuthService._get_user_by_phone(db, "+51987654321")
        """
        result = await db.execute(
            select(User).where(User.phone_number == phone_number)
        )
        return result.scalar_one_or_none()