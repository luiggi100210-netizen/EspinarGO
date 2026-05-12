"""
Endpoints del módulo de autenticación.

Todas las rutas bajo /api/v1/auth/
Este archivo solo llama a AuthService y OTPService.
No contiene lógica de negocio propia.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import hash_password, verify_password
from app.middleware.auth import get_current_active_user
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RefreshTokenResponse,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    SendOTPRequest,
    SendOTPResponse,
    SessionOut,
    TokenResponse,
    VerifyOTPRequest,
    VerifyOTPResponse,
)
from app.schemas.base import MessageResponse
from app.schemas.user import UserProfile, UserPublicOut
from app.services.auth_service import AuthService
from app.services.otp_service import OTPService
from app.utils.rate_limit import check_login_rate_limit, check_register_rate_limit

router = APIRouter(
    prefix="/auth",
    tags=["Autenticación"],
)


@router.get("/health")
async def health_check():
    """
    Health check del servicio de autenticación.

    Usado por Railway y UptimeRobot para monitoreo.
    """
    return {
        "status": "ok",
        "module": "auth",
        "version": "1.0.0",
    }


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=RegisterResponse,
    summary="Crear cuenta nueva",
    description="Crea una cuenta nueva. Tras el registro se envía "
    "un código OTP por SMS para verificar el teléfono.",
)
async def register(
    data: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Registro de nuevo usuario.

    El usuario recibe un código SMS para verificar su número.
    """
    ip = request.client.host if request.client else "unknown"
    allowed, wait = await check_register_rate_limit(ip)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Demasiados registros. Intenta en {wait // 60 + 1} minuto(s).",
        )

    try:
        user = await AuthService.register(db, data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return RegisterResponse(
        message="Cuenta creada. Se envió un código de verificación.",
        user_id=user.id,
        phone_number=user.phone_number,
        next_step="verify_phone",
    )


@router.post(
    "/send-otp",
    response_model=SendOTPResponse,
    summary="Enviar código de verificación por SMS",
)
async def send_otp(
    data: SendOTPRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Envía un código OTP al número de teléfono del usuario.

    El código puede ser para verificar teléfono, login o reset de contraseña.
    """
    result = await db.execute(
        select(User).where(User.phone_number == data.phone_number)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay cuenta con este número. Regístrate primero.",
        )

    try:
        response = await OTPService.send_otp(db, user, data.purpose)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e),
        )

    return SendOTPResponse(**response)


@router.post(
    "/verify-phone",
    response_model=VerifyOTPResponse,
    summary="Verificar número de teléfono con código SMS",
)
async def verify_phone(
    data: VerifyOTPRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Verifica el número de teléfono con el código OTP.
    """
    try:
        result = await AuthService.verify_phone(
            db, data.phone_number, data.code
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return VerifyOTPResponse(
        message=result["message"],
        verified=True,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Iniciar sesión",
    description="Retorna access_token (30 min) y refresh_token (30 días)",
)
async def login(
    data: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Inicia sesión con número de teléfono y contraseña.

    Retorna tokens para autenticación en futuras requests.
    """
    ip_address = request.client.host if request.client else "unknown"
    allowed, wait = await check_login_rate_limit(ip_address)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Demasiados intentos. Intenta en {wait // 60 + 1} minuto(s).",
        )

    try:
        result = await AuthService.login(db, data, ip_address)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )

    return {
        "access_token": result["access_token"],
        "refresh_token": result["refresh_token"],
        "token_type": result["token_type"],
        "expires_in": result["expires_in"],
        "user": UserPublicOut.model_validate(result["user"]),
    }


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    summary="Renovar access token sin pedir contraseña",
)
async def refresh_token(
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Usa el refresh token para obtener un nuevo access token.
    """
    try:
        result = await AuthService.refresh_access_token(
            db, data.refresh_token
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )

    return RefreshTokenResponse(**result)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Cerrar sesión en este dispositivo",
)
async def logout(
    data: RefreshTokenRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Cierra la sesión en el dispositivo actual.
    """
    await AuthService.logout(db, data.refresh_token)

    return MessageResponse(message="Sesión cerrada correctamente")


@router.post(
    "/logout-all",
    response_model=MessageResponse,
    summary="Cerrar sesión en todos los dispositivos",
)
async def logout_all(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Cierra todas las sesiones del usuario en todos los dispositivos.
    """
    await AuthService.logout_all_devices(db, current_user.id)

    return MessageResponse(
        message="Sesiones cerradas en todos los dispositivos"
    )


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Solicitar código para restablecer contraseña",
)
async def forgot_password(
    data: SendOTPRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Solicita un código OTP para recuperar la contraseña.

    Siempre retorna mensaje genérico por seguridad.
    """
    await AuthService.request_password_reset(db, data.phone_number)

    return MessageResponse(
        message="Si el número está registrado, "
        "recibirás un código SMS en breve."
    )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Establecer nueva contraseña con código OTP",
)
async def reset_password(
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Restablece la contraseña usando el código OTP.
    """
    try:
        result = await AuthService.reset_password(
            db,
            data.phone_number,
            data.otp_code,
            data.new_password,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return MessageResponse(message=result["message"])


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Cambiar contraseña (usuario autenticado)",
)
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Cambia la contraseña actual por una nueva.
    """
    if not verify_password(
        data.current_password, current_user.password_hash or ""
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contraseña actual incorrecta",
        )

    current_user.password_hash = hash_password(data.new_password)

    await AuthService.logout_all_devices(db, current_user.id)

    return MessageResponse(
        message="Contraseña actualizada. Inicia sesión de nuevo."
    )


@router.get(
    "/me",
    response_model=UserProfile,
    summary="Obtener mi perfil completo",
)
async def get_my_profile(
    current_user: User = Depends(get_current_active_user),
):
    """
    Retorna los datos completos del usuario autenticado.
    """
    return UserProfile.model_validate(current_user)


@router.get(
    "/sessions",
    response_model=list[SessionOut],
    summary="Listar sesiones activas",
)
async def list_sessions(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna todas las sesiones activas del usuario (dispositivos con sesión abierta).
    """
    sessions = await AuthService.get_sessions(db, current_user.id)
    return [SessionOut.model_validate(s) for s in sessions]


@router.delete(
    "/sessions/{session_id}",
    response_model=MessageResponse,
    summary="Cerrar sesión en un dispositivo específico",
)
async def revoke_session(
    session_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Cierra la sesión en un dispositivo específico revocando su refresh token.
    """
    try:
        await AuthService.revoke_session(db, session_id, current_user.id)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return MessageResponse(message="Sesión cerrada correctamente")