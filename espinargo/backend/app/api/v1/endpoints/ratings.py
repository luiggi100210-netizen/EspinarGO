"""
Endpoints para el sistema de calificaciones mutuas.

Tras cada viaje completado, pasajero y conductor se califican.

Rutas bajo /api/v1/ratings/
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_active_user
from app.models.user import User
from app.schemas.rating import RatingPublic, RatingRequest, RatingSummary
from app.services.rating_service import RatingService

router = APIRouter(
    prefix="/ratings",
    tags=["Calificaciones"],
)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=RatingPublic,
    summary="Calificar un viaje completado",
)
async def create_rating(
    data: RatingRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Califica un viaje completado.
    El pasajero califica al conductor o viceversa.
    """
    try:
        return await RatingService.create_rating(db, current_user, data)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/received",
    response_model=list[RatingPublic],
    summary="Ver calificaciones que recibí",
)
async def get_received_ratings(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retorna las calificaciones que el usuario ha recibido."""
    return await RatingService.get_received_ratings(db, current_user, page, per_page)


@router.get(
    "/given",
    response_model=list[RatingPublic],
    summary="Ver calificaciones que di",
)
async def get_given_ratings(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retorna las calificaciones que el usuario ha dado a otros."""
    return await RatingService.get_given_ratings(db, current_user, page, per_page)


@router.get(
    "/summary/{user_id}",
    response_model=RatingSummary,
    summary="Ver resumen de calificaciones de un usuario",
)
async def get_rating_summary(
    user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna el resumen de calificaciones de un usuario.
    Incluye promedio, total y distribución por estrellas.
    """
    try:
        return await RatingService.get_rating_summary(db, user_id)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))