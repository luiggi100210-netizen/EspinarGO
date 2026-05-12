"""
Servicio de calificaciones — lógica de negocio del sistema de ratings.

Tras cada viaje completado, pasajero y conductor se califican mutuamente.

Los endpoints solo orquestan HTTP; toda la lógica vive aquí.
"""

from uuid import UUID

from sqlalchemy import case, func, select
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
            raise LookupError("Viaje no encontrado")
        if trip.status != TripStatus.COMPLETED:
            raise ValueError("Solo puedes calificar viajes completados")

        is_passenger = trip.passenger_id == user.id
        is_driver = trip.driver_id == user.id if trip.driver_id else False

        if not is_passenger and not is_driver:
            raise PermissionError("No participaste en este viaje")

        rating_type = RatingType.PASSENGER_TO_DRIVER if is_passenger else RatingType.DRIVER_TO_PASSENGER
        rated_id = trip.driver_id if is_passenger else trip.passenger_id

        if not rated_id:
            raise ValueError("El viaje no tiene un participante válido para calificar")

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
    async def get_rating_summary(db: AsyncSession, user_id: UUID) -> RatingSummary:
        user = await db.get(User, user_id)
        if not user:
            raise LookupError("Usuario no encontrado")

        row = (
            await db.execute(
                select(
                    func.count().label("total"),
                    func.avg(Rating.score).label("average"),
                    func.sum(case((Rating.score == 5, 1), else_=0)).label("five_stars"),
                    func.sum(case((Rating.score == 4, 1), else_=0)).label("four_stars"),
                    func.sum(case((Rating.score == 3, 1), else_=0)).label("three_stars"),
                    func.sum(case((Rating.score == 2, 1), else_=0)).label("two_stars"),
                    func.sum(case((Rating.score == 1, 1), else_=0)).label("one_star"),
                ).where(Rating.rated_id == user_id)
            )
        ).one()

        if not row.total:
            return RatingSummary(
                average_score=0.0,
                total_ratings=0,
                five_stars=0,
                four_stars=0,
                three_stars=0,
                two_stars=0,
                one_star=0,
            )

        return RatingSummary(
            average_score=round(float(row.average), 1),
            total_ratings=row.total,
            five_stars=row.five_stars or 0,
            four_stars=row.four_stars or 0,
            three_stars=row.three_stars or 0,
            two_stars=row.two_stars or 0,
            one_star=row.one_star or 0,
        )

    @staticmethod
    async def get_given_ratings(
        db: AsyncSession,
        user: User,
        page: int,
        per_page: int,
    ) -> list[RatingPublic]:
        ratings = (
            await db.execute(
                select(Rating)
                .where(Rating.rater_id == user.id)
                .order_by(Rating.created_at.desc())
                .offset((page - 1) * per_page)
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
                rater=UserPublicOut.model_validate(user),
            )
            for r in ratings
        ]
