"""
Endpoints para el sistema de calificaciones mutuas.

Tras cada viaje completado, pasajero y conductor se califican.

Rutas bajo /api/v1/ratings/
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_active_user
from app.models.rating import Rating, RatingType
from app.models.trip import Trip, TripStatus
from app.models.user import DriverProfile, User
from app.schemas.rating import RatingPublic, RatingRequest, RatingSummary
from app.schemas.user import UserPublicOut

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
    trip = await db.get(Trip, data.trip_id)

    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Viaje no encontrado",
        )

    if trip.status != TripStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo puedes calificar viajes completados",
        )

    is_passenger = trip.passenger_id == current_user.id
    is_driver = trip.driver_id == current_user.id if trip.driver_id else False

    if not is_passenger and not is_driver:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No participaste en este viaje",
        )

    if is_passenger:
        rating_type = RatingType.PASSENGER_TO_DRIVER
        rated_id = trip.driver_id
    else:
        rating_type = RatingType.DRIVER_TO_PASSENGER
        rated_id = trip.passenger_id

    existing = await db.execute(
        select(Rating).where(
            Rating.trip_id == data.trip_id,
            Rating.rater_id == current_user.id,
            Rating.rating_type == rating_type,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya calificaste este viaje",
        )

    rating = Rating(
        trip_id=data.trip_id,
        rater_id=current_user.id,
        rated_id=rated_id,
        rating_type=rating_type,
        score=data.score,
        comment=data.comment,
    )

    db.add(rating)
    await db.flush()

    if rating_type == RatingType.PASSENGER_TO_DRIVER:
        dp_result = await db.execute(
            select(DriverProfile).where(DriverProfile.user_id == rated_id)
        )
        dp = dp_result.scalar_one_or_none()
        if dp:
            dp.rating = round((dp.rating * dp.rating_count + data.score * 10) / (dp.rating_count + 1))
            dp.rating_count += 1

    return RatingPublic(
        id=rating.id,
        score=rating.score,
        comment=rating.comment,
        rating_type=rating.rating_type.value,
        created_at=rating.created_at,
        rater=UserPublicOut.model_validate(current_user),
    )


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
    """
    Retorna las calificaciones que el usuario ha recibido.
    """
    offset = (page - 1) * per_page

    result = await db.execute(
        select(Rating)
        .where(Rating.rated_id == current_user.id)
        .order_by(Rating.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    ratings = result.scalars().all()

    return [
        RatingPublic(
            id=r.id,
            score=r.score,
            comment=r.comment,
            rating_type=r.rating_type.value,
            created_at=r.created_at,
            rater=UserPublicOut.model_validate(r.rater) if r.rater else None,
        )
        for r in ratings
    ]


@router.get(
    "/summary/{user_id}",
    response_model=RatingSummary,
    summary="Ver resumen de calificaciones de un usuario",
)
async def get_rating_summary(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna el resumen de calificaciones de un usuario.
    Incluye promedio, total y distribución por estrellas.
    """
    result = await db.execute(
        select(Rating).where(Rating.rated_id == user_id)
    )
    ratings = result.scalars().all()

    if not ratings:
        return RatingSummary(
            average_score=0.0,
            total_ratings=0,
            five_stars=0,
            four_stars=0,
            three_stars=0,
            two_stars=0,
            one_star=0,
        )

    total = len(ratings)
    total_score = sum(r.score for r in ratings)
    average = round(total_score / total, 1)

    five_stars = sum(1 for r in ratings if r.score == 5)
    four_stars = sum(1 for r in ratings if r.score == 4)
    three_stars = sum(1 for r in ratings if r.score == 3)
    two_stars = sum(1 for r in ratings if r.score == 2)
    one_star = sum(1 for r in ratings if r.score == 1)

    return RatingSummary(
        average_score=average,
        total_ratings=total,
        five_stars=five_stars,
        four_stars=four_stars,
        three_stars=three_stars,
        two_stars=two_stars,
        one_star=one_star,
    )