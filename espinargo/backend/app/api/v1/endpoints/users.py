"""
Endpoints para gestión de perfiles de usuario.

Actualizar datos personales, foto de perfil,
datos del vehículo del conductor y sus documentos.

Rutas bajo /api/v1/users/
"""

import cloudinary
import cloudinary.uploader
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
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
    DriverProfilePublic,
    UpdateAvatarResponse,
    UpdateProfileRequest,
    UpdateVehicleRequest,
    UploadDocumentResponse,
    UserProfile,
)
from app.utils.serializers import driver_profile_to_public
from sqlalchemy import select

router = APIRouter(
    prefix="/users",
    tags=["Usuarios"],
)

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
)


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
    if not file.content_type.startswith("image/"):
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

    result = cloudinary.uploader.upload(
        contents,
        folder=f"espinargo/avatars/{current_user.id}",
        public_id=str(current_user.id),
        overwrite=True,
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
    if not (content_type.startswith("image/") or content_type == "application/pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se permiten imágenes o archivos PDF",
        )

    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El documento no puede superar 10MB",
        )

    result = cloudinary.uploader.upload(
        contents,
        folder=f"espinargo/documents/{current_user.id}",
        public_id=document_type,
        overwrite=True,
    )

    driver_profile = current_user.driver_profile
    field_name = DOCUMENT_TYPES[document_type]
    setattr(driver_profile, field_name, result["secure_url"])

    current_docs = {
        doc: getattr(driver_profile, DOCUMENT_TYPES[doc])
        for doc in REQUIRED_DOCS
    }

    if all(current_docs.values()) and driver_profile.driver_status.value == "pending_docs":
        driver_profile.driver_status = DriverStatus.UNDER_REVIEW

    return UploadDocumentResponse(
        message="Documento subido correctamente",
        document_type=document_type,
        url=result["secure_url"],
        driver_status=driver_profile.driver_status.value,
    )


@router.get(
    "/drivers/{driver_id}",
    response_model=DriverProfilePublic,
    summary="Ver perfil público de un conductor",
)
async def get_driver_profile(
    driver_id: str,
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

    if driver_profile.driver_status.value != "approved":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conductor no encontrado",
        )

    return driver_profile_to_public(driver_profile)