"""
Servicio de calificaciones — lógica de negocio del sistema de ratings.

Tras cada viaje completado, pasajero y conductor se califican mutuamente.

Los endpoints solo orquestan HTTP; toda la lógica vive aquí.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rating import Rating, RatingType
from app.models.trip import Trip, TripStatus
from app.models.user import DriverProfile, User
from app.schemas.rating import RatingPublic, RatingRequest, RatingSummary
from app.schemas.user import UserPublicOut


class RatingService:
    @staticmethod
    async def create_rating(
        db: AsyncSession, user: User, data: RatingRequest
    ) -> RatingPublic:
        trip = await db.get(Trip, data.trip_id)

        if not trip:
            raise ValueError("Viaje no encontrado")
        if trip.status != TripStatus.COMPLETED:
            raise ValueError("Solo puedes calificar viajes completados")

        is_passenger = trip.passenger_id == user.id
        is_driver = trip.driver_id == user.id if trip.driver_id else False

        if not is_passenger and not is_driver:
            raise PermissionError("No participaste en este viaje")

        rating_type = RatingType.PASSENGER_TO_DRIVER if is_passenger else RatingType.DRIVER_TO_PASSENGER
        rated_id = trip.driver_id if is_passenger else trip.passenger_id

        existing = (
            await db.execute(
                select(Rating).where(
                    Rating.trip_id == data.trip_id,
                    Rating.rater_id == user.id,
                    Rating.rating_type == rating_type,
                )
            )
        ).scalar_one_or_none()

        if existing:
            raise ValueError("Ya calificaste este viaje")

        rating = Rating(
            trip_id=data.trip_id,
            rater_id=user.id,
            rated_id=rated_id,
            rating_type=rating_type,
            score=data.score,
            comment=data.comment,
        )
        db.add(rating)
        await db.flush()

        if rating_type == RatingType.PASSENGER_TO_DRIVER:
            dp = (
                await db.execute(
                    select(DriverProfile).where(DriverProfile.user_id == rated_id)
                )
            ).scalar_one_or_none()
            if dp:
                dp.rating = round(
                    (dp.rating * dp.rating_count + data.score * 10) / (dp.rating_count + 1)
                )
                dp.rating_count += 1

        await db.commit()

        return RatingPublic(
            id=rating.id,
            score=rating.score,
            comment=rating.comment,
            rating_type=rating.rating_type.value,
            created_at=rating.created_at,
            rater=UserPublicOut.model_validate(user),
        )

    @staticmethod
    async def get_received_ratings(
        db: AsyncSession,
        user: User,
        page: int,
        per_page: int,
    ) -> list[RatingPublic]:
        offset = (page - 1) * per_page

        ratings = (
            await db.execute(
                select(Rating)
                .where(Rating.rated_id == user.id)
                .order_by(Rating.created_at.desc())
                .offset(offset)
                .limit(per_page)
            )
        ).scalars().all()

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

    @staticmethod
    async def get_rating_summary(db: AsyncSession, user_id: str) -> RatingSummary:
        ratings = (
            await db.execute(select(Rating).where(Rating.rated_id == user_id))
        ).scalars().all()

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
        average = round(sum(r.score for r in ratings) / total, 1)

        return RatingSummary(
            average_score=average,
            total_ratings=total,
            five_stars=sum(1 for r in ratings if r.score == 5),
            four_stars=sum(1 for r in ratings if r.score == 4),
            three_stars=sum(1 for r in ratings if r.score == 3),
            two_stars=sum(1 for r in ratings if r.score == 2),
            one_star=sum(1 for r in ratings if r.score == 1),
        )
