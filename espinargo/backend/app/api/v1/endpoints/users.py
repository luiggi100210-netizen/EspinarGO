"""
Endpoints para gestión de perfiles de usuario.

Actualizar datos personales, foto de perfil,
datos del vehículo del conductor y sus documentos.

Rutas bajo /api/v1/users/
"""

import asyncio
from uuid import UUID

import cloudinary
import cloudinary.uploader
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.middleware.auth import (
    get_current_active_user,
    get_current_driver,
)
from app.models.user import DriverProfile, DriverStatus, User, UserStatus
from app.schemas.base import MessageResponse
from app.schemas.user import (
    DocumentStatusResponse,
    DriverProfilePublic,
    UpdateAvatarResponse,
    UpdateOnlineStatusRequest,
    UpdateProfileRequest,
    UpdateVehicleRequest,
    UploadDocumentResponse,
    UserProfile,
)
from app.utils.serializers import driver_profile_to_public

router = APIRouter(
    prefix="/users",
    tags=["Usuarios"],
)

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
)


@router.get(
    "/me/driver-profile",
    response_model=DriverProfilePublic,
    summary="Ver mi perfil de conductor",
)
async def get_my_driver_profile(
    current_user: User = Depends(get_current_driver),
    db: AsyncSession = Depends(get_db),
):
    """Retorna el perfil de conductor del usuario autenticado."""
    driver_profile = current_user.driver_profile
    if not driver_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No tienes perfil de conductor",
        )
    return driver_profile_to_public(driver_profile)


@router.patch(
    "/me",
    response_model=UserProfile,
    summary="Actualizar datos del perfil",
)
async def update_profile(
    data: UpdateProfileRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Actualiza los campos del perfil que se envíen en el request.
    """
    update_data = data.model_dump(exclude_unset=True)

    if "email" in update_data and update_data["email"]:
        existing = (
            await db.execute(
                select(User).where(
                    User.email == update_data["email"],
                    User.id != current_user.id,
                )
            )
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El correo electrónico ya está en uso",
            )

    for field, value in update_data.items():
        setattr(current_user, field, value)

    return UserProfile.model_validate(current_user)


@router.post(
    "/me/avatar",
    response_model=UpdateAvatarResponse,
    summary="Subir foto de perfil",
)
async def upload_avatar(
    file: UploadFile,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Sube una imagen como foto de perfil.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se permiten archivos de imagen",
        )

    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La imagen no puede superar 5MB",
        )

    if not any(contents.startswith(sig) for sig in _IMAGE_SIGNATURES):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo no es una imagen válida",
        )

    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        None,
        lambda: cloudinary.uploader.upload(
            contents,
            folder=f"espinargo/avatars/{current_user.id}",
            public_id=str(current_user.id),
            overwrite=True,
        ),
    )

    current_user.avatar_url = result["secure_url"]

    return UpdateAvatarResponse(
        message="Foto de perfil actualizada",
        avatar_url=result["secure_url"],
    )


@router.patch(
    "/me/vehicle",
    response_model=DriverProfilePublic,
    summary="Actualizar datos del vehículo",
)
async def update_vehicle(
    data: UpdateVehicleRequest,
    current_user: User = Depends(get_current_driver),
    db: AsyncSession = Depends(get_db),
):
    """
    Actualiza los datos del vehículo del conductor.
    """
    driver_profile = current_user.driver_profile

    if not driver_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No tienes perfil de conductor",
        )

    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(driver_profile, field, value)

    return driver_profile_to_public(driver_profile)


_IMAGE_SIGNATURES = (
    b"\xff\xd8\xff",        # JPEG
    b"\x89PNG\r\n\x1a\n",  # PNG
    b"GIF87a",              # GIF
    b"GIF89a",              # GIF
    b"RIFF",                # WebP
)
_PDF_SIGNATURE = b"%PDF"

DOCUMENT_TYPES = {
    "dni_front": "dni_front_url",
    "dni_back": "dni_back_url",
    "license": "license_url",
    "soat": "soat_url",
    "property_card": "property_card_url",
    "selfie": "selfie_url",
    "vehicle_photo": "vehicle_photo_url",
}

REQUIRED_DOCS = {"dni_front", "dni_back", "license", "soat", "selfie"}


@router.post(
    "/me/documents/{document_type}",
    response_model=UploadDocumentResponse,
    summary="Subir documento de conductor",
)
async def upload_document(
    document_type: str,
    file: UploadFile,
    current_user: User = Depends(get_current_driver),
    db: AsyncSession = Depends(get_db),
):
    """
    Sube documentos requeridos del conductor (DNI, licencia, etc.).
    """
    if document_type not in DOCUMENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de documento inválido. Tipos válidos: {', '.join(DOCUMENT_TYPES.keys())}",
        )

    content_type = file.content_type
    if not content_type or not (content_type.startswith("image/") or content_type == "application/pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se permiten imágenes o archivos PDF",
        )

    driver_profile = current_user.driver_profile
    if not driver_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No tienes perfil de conductor",
        )

    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El documento no puede superar 10MB",
        )

    is_image = any(contents.startswith(sig) for sig in _IMAGE_SIGNATURES)
    is_pdf = contents.startswith(_PDF_SIGNATURE)
    if not is_image and not is_pdf:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo no es una imagen o PDF válido",
        )

    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        None,
        lambda: cloudinary.uploader.upload(
            contents,
            folder=f"espinargo/documents/{current_user.id}",
            public_id=document_type,
            overwrite=True,
        ),
    )

    field_name = DOCUMENT_TYPES[document_type]
    setattr(driver_profile, field_name, result["secure_url"])

    current_docs = {
        doc: getattr(driver_profile, DOCUMENT_TYPES[doc])
        for doc in REQUIRED_DOCS
    }

    resubmittable = (DriverStatus.PENDING_DOCS, DriverStatus.REJECTED)
    if all(current_docs.values()) and driver_profile.driver_status in resubmittable:
        driver_profile.driver_status = DriverStatus.UNDER_REVIEW

    return UploadDocumentResponse(
        message="Documento subido correctamente",
        document_type=document_type,
        url=result["secure_url"],
        driver_status=driver_profile.driver_status.value,
    )


@router.patch(
    "/me/online",
    response_model=MessageResponse,
    summary="Activar o desactivar disponibilidad como conductor",
)
async def update_online_status(
    data: UpdateOnlineStatusRequest,
    current_user: User = Depends(get_current_driver),
    db: AsyncSession = Depends(get_db),
):
    """
    El conductor activa o desactiva su disponibilidad para recibir viajes.
    """
    driver_profile = current_user.driver_profile
    if not driver_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No tienes perfil de conductor",
        )

    if driver_profile.driver_status != DriverStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu cuenta de conductor no está aprobada",
        )

    driver_profile.is_online = data.is_online
    estado = "en línea" if data.is_online else "fuera de línea"
    return MessageResponse(message=f"Ahora estás {estado}")


@router.get(
    "/me/documents",
    response_model=DocumentStatusResponse,
    summary="Ver estado de documentos subidos",
)
async def get_my_documents(
    current_user: User = Depends(get_current_driver),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna el estado actual de los documentos del conductor.
    """
    driver_profile = current_user.driver_profile
    if not driver_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No tienes perfil de conductor",
        )

    return DocumentStatusResponse(
        dni_front_url=driver_profile.dni_front_url,
        dni_back_url=driver_profile.dni_back_url,
        license_url=driver_profile.license_url,
        soat_url=driver_profile.soat_url,
        selfie_url=driver_profile.selfie_url,
        property_card_url=driver_profile.property_card_url,
        vehicle_photo_url=driver_profile.vehicle_photo_url,
        driver_status=driver_profile.driver_status.value,
        rejection_reason=driver_profile.rejection_reason,
    )


@router.get(
    "/drivers/{driver_id}",
    response_model=DriverProfilePublic,
    summary="Ver perfil público de un conductor",
)
async def get_driver_profile(
    driver_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna el perfil público de un conductor.
    Solo muestra conductors aprobados.
    """
    result = await db.execute(
        select(DriverProfile).where(DriverProfile.user_id == driver_id)
    )
    driver_profile = result.scalar_one_or_none()

    if not driver_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conductor no encontrado",
        )

    if driver_profile.driver_status != DriverStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conductor no encontrado",
        )

    return driver_profile_to_public(driver_profile)