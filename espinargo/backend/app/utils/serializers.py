"""
Funciones de serialización compartidas entre endpoints.

Centraliza la conversión de modelos SQLAlchemy a schemas Pydantic
para evitar duplicación en endpoints de trips, packages y users.
"""

from app.models.package import Package
from app.models.trip import Trip
from app.models.user import DriverProfile
from app.schemas.package import PackagePublic
from app.schemas.trip import TripPublic
from app.schemas.user import DriverProfilePublic, UserPublicOut


def trip_to_public(trip: Trip) -> TripPublic:
    return TripPublic(
        id=trip.id,
        passenger=UserPublicOut.model_validate(trip.passenger) if trip.passenger else None,
        driver=UserPublicOut.model_validate(trip.driver) if trip.driver else None,
        origin_address=trip.origin_address,
        dest_address=trip.dest_address,
        proposed_price=trip.proposed_price,
        final_price=trip.final_price,
        status=trip.status.value,
        payment_method=trip.payment_method,
        distance_km=trip.distance_km,
        duration_minutes=trip.duration_minutes,
        created_at=trip.created_at,
        accepted_at=trip.accepted_at,
        started_at=trip.started_at,
        completed_at=trip.completed_at,
    )


def driver_profile_to_public(dp: DriverProfile | None) -> DriverProfilePublic | None:
    if not dp:
        return None
    return DriverProfilePublic(
        id=dp.id,
        vehicle_type=dp.vehicle_type,
        vehicle_brand=dp.vehicle_brand,
        vehicle_model=dp.vehicle_model,
        vehicle_year=dp.vehicle_year,
        vehicle_color=dp.vehicle_color,
        vehicle_plate=dp.vehicle_plate,
        vehicle_photo_url=dp.vehicle_photo_url,
        driver_status=dp.driver_status.value,
        rating_display=dp.rating_display,
        total_trips=dp.total_trips,
        is_online=dp.is_online,
    )


def package_to_public(pkg: Package) -> PackagePublic:
    return PackagePublic(
        id=pkg.id,
        tracking_code=pkg.tracking_code,
        sender=UserPublicOut.model_validate(pkg.sender) if pkg.sender else None,
        driver=UserPublicOut.model_validate(pkg.driver) if pkg.driver else None,
        recipient_name=pkg.recipient_name,
        recipient_phone=pkg.recipient_phone,
        delivery_address=pkg.delivery_address,
        size=pkg.size.value,
        description=pkg.description,
        is_fragile=pkg.is_fragile,
        status=pkg.status.value,
        price=pkg.price,
        payment_method=pkg.payment_method,
        created_at=pkg.created_at,
        picked_up_at=pkg.picked_up_at,
        delivered_at=pkg.delivered_at,
    )
