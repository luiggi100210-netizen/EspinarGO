"""
Punto de entrada para exportar todos los modelos de la aplicación.

Este archivo es crítico para que Alembic detecte los modelos
al generar las migraciones. El orden de importación importa
porque algunos modelos tienen relaciones con otros.

Orden de importación (importante por dependencias):
1. Base desde app.core.database (debe importarse primero)
2. Enums de app.models.user (usados en varios modelos)
3. Modelos de user.py (no dependen de otros modelos)
4. Modelos de trip.py (depende de user.py)
5. Modelos de package.py (depende de user.py)
6. Modelos de rating.py (depende de user.py y trip.py)
"""

from app.core.database import Base
from app.models.user import (
    DriverProfile,
    DriverStatus,
    OTPCode,
    RefreshToken,
    User,
    UserRole,
    UserStatus,
    VehicleType,
)
from app.models.trip import (
    PaymentMethod,
    Trip,
    TripCancelReason,
    TripOffer,
    TripStatus,
)
from app.models.package import (
    Package,
    PackageSize,
    PackageStatus,
    PackageTracking,
)
from app.models.rating import Rating, RatingType

__all__ = [
    "Base",
    "UserRole",
    "UserStatus",
    "DriverStatus",
    "VehicleType",
    "User",
    "RefreshToken",
    "OTPCode",
    "DriverProfile",
    "TripStatus",
    "TripCancelReason",
    "PaymentMethod",
    "Trip",
    "TripOffer",
    "PackageSize",
    "PackageStatus",
    "Package",
    "PackageTracking",
    "RatingType",
    "Rating",
]