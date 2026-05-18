"""
Dependencias de FastAPI para proteger rutas con autenticación.

Este archivo contiene las funciones que actúan como "portero" de la API:
deciden quién puede acceder a cada endpoint verificando el token JWT
y el estado de la cuenta del usuario.

Cada función es una dependencia que se inyecta en los endpoints
con Depends() para proteger las rutas.
"""

from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import PyJWTError as JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User, UserRole, UserStatus
from app.services.otp_service import get_redis

# =============================================================================
# CONFIGURACIÓN DE SEGURIDAD
# =============================================================================

security = HTTPBearer(auto_error=False)

"""
HTTPBearer para extraer el token del header Authorization.

auto_error=False permite manejar el error de forma personalizada
en español en lugar del error genérico de FastAPI.
"""

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Token inválido o expirado. Inicia sesión de nuevo.",
    headers={"WWW-Authenticate": "Bearer"},
)

"""
Excepción para cuando el token es inválido o expiró.

Se reutiliza en varias funciones para mantener consistencia
en los mensajes de error.
"""

INACTIVE_EXCEPTION = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Tu cuenta está inactiva o suspendida.",
)

"""
Excepción para cuando la cuenta del usuario está suspendida o baneada.
"""


# =============================================================================
# DEPENDENCIAS DE AUTENTICACIÓN
# =============================================================================


async def get_token_payload(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """
    Extrae y valida el payload del token JWT.

    Verifica que el token exista, que sea del tipo correcto (access),
    y que no esté expirado o modificado.

    Args:
        credentials: Credenciales del header Authorization (inyectado por FastAPI).

    Returns:
        dict: Payload del token con los datos del usuario.

    Raises:
        HTTPException: Si el token es inválido, expirado, o no es de tipo access.

    Example:
        >>> @app.get("/ruta-protegida")
        ... async def mi_ruta(payload: dict = Depends(get_token_payload)):
        ...     user_id = payload["sub"]
    """
    if not credentials or credentials.scheme.lower() != "bearer":
        raise CREDENTIALS_EXCEPTION

    try:
        payload = decode_access_token(credentials.credentials)
    except JWTError:
        raise CREDENTIALS_EXCEPTION

    jti = payload.get("jti")
    if jti:
        redis = await get_redis()
        if await redis.exists(f"revoked_jti:{jti}"):
            raise CREDENTIALS_EXCEPTION

    return payload


async def get_current_user(
    payload: dict = Depends(get_token_payload),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Obtiene el usuario actual a partir del token JWT.

    Verifica que el usuario exista en la base de datos y que su
    cuenta esté activa. Esta es la dependencia principal para
    proteger rutas.

    Args:
        payload: Payload del token decodificado.
        db: Sesión de base de datos.

    Returns:
        User: Usuario autenticado.

    Raises:
        HTTPException: Si el token es inválido, el usuario no existe,
                       o la cuenta está inactiva.

    Example:
        >>> @router.get("/perfil")
        ... async def mi_perfil(user: User = Depends(get_current_user)):
        ...     return {"nombre": user.full_name}
    """
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise CREDENTIALS_EXCEPTION

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise CREDENTIALS_EXCEPTION

    user = await db.get(User, user_id)

    if not user:
        raise CREDENTIALS_EXCEPTION

    if user.status in (UserStatus.SUSPENDED, UserStatus.BANNED):
        raise INACTIVE_EXCEPTION

    return user


async def get_current_active_user(
    user: User = Depends(get_current_user),
) -> User:
    """
    Verifica que el usuario tenga el teléfono verificado y cuenta activa.

    Diferencia con get_current_user: también verifica phone_verified.
    Útil para rutas donde el usuario necesita haber completado el registro.

    Args:
        user: Usuario de Depends(get_current_user).

    Returns:
        User: Usuario con cuenta activa y verificada.

    Raises:
        HTTPException: Si el teléfono no está verificado o la cuenta no está activa.

    Example:
        >>> @router.post("/solicitar-viaje")
        ... async def solicitar_viaje(
        ...     user: User = Depends(get_current_active_user)
        ... ):
        ...     pass  # El usuario puede solicitar viajes
    """
    if not user.phone_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Debes verificar tu número de teléfono para continuar.",
        )

    if user.status != UserStatus.ACTIVE:
        raise INACTIVE_EXCEPTION

    return user


async def get_current_passenger(
    user: User = Depends(get_current_active_user),
) -> User:
    """
    Verifica que el usuario sea pasajero (o administrador).

    Los administradores también pueden acceder a rutas de pasajero
    para pruebas y soporte técnico.

    Args:
        user: Usuario de Depends(get_current_active_user).

    Returns:
        User: Usuario con rol de pasajero.

    Raises:
        HTTPException: Si el usuario no es pasajero ni admin.

    Example:
        >>> @router.get("/mis-viajes")
        ... async def mis_viajes(
        ...     user: User = Depends(get_current_passenger)
        ... ):
        ...     pass  # Solo pasajeros pueden ver sus viajes
    """
    if user.role not in (UserRole.PASSENGER, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso solo para pasajeros.",
        )

    return user


async def get_current_driver(
    user: User = Depends(get_current_active_user),
) -> User:
    """
    Verifica que el usuario sea conductor (o administrador).

    Los administradores también pueden acceder a rutas de conductor
    para pruebas y soporte técnico.

    Args:
        user: Usuario de Depends(get_current_active_user).

    Returns:
        User: Usuario con rol de conductor.

    Raises:
        HTTPException: Si el usuario no es conductor ni admin.

    Example:
        >>> @router.get("/mis-ofertas")
        ... async def mis_ofertas(
        ...     user: User = Depends(get_current_driver)
        ... ):
        ...     pass  # Solo conductores pueden ver sus ofertas
    """
    if user.role not in (UserRole.DRIVER, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso solo para conductores.",
        )

    return user


async def get_current_admin(
    user: User = Depends(get_current_active_user),
) -> User:
    """
    Verifica que el usuario sea administrador.

    Esta es la dependencia más restrictiva: solo admins pueden acceder.
    Se usa para rutas de gestión de usuarios, aprobación de conductores, etc.

    Args:
        user: Usuario de Depends(get_current_active_user).

    Returns:
        User: Usuario con rol de administrador.

    Raises:
        HTTPException: Si el usuario no es administrador.

    Example:
        >>> @router.get("/usuarios")
        ... async def listar_usuarios(
        ...     admin: User = Depends(get_current_admin)
        ... ):
        ...     pass  # Solo admins pueden listar usuarios
    """
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso de administrador requerido.",
        )

    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Obtiene el usuario si está autenticado, o None si no.

    Útil para rutas públicas que muestran contenido diferente
    dependiendo de si el usuario está logueado o no.
    No lanza error si el token es inválido, simplemente retorna None.

    Args:
        credentials: Credenciales del header Authorization (opcional).
        db: Sesión de base de datos.

    Returns:
        Optional[User]: Usuario si está autenticado, None si no.

    Example:
        >>> @router.get("/")
        ... async def inicio(
        ...     user: Optional[User] = Depends(get_optional_user)
        ... ):
        ...     if user:
        ...         return f"Bienvenido, {user.full_name}"
        ...     return "Inicia sesión para continuar"
    """
    if not credentials:
        return None

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = UUID(payload.get("sub", ""))
        user = await db.get(User, user_id)
        return user if user and user.status == UserStatus.ACTIVE else None
    except (JWTError, ValueError, TypeError):
        return None