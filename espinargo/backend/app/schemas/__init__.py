"""
Punto de entrada para exportar todos los schemas de la aplicación.

Este archivo permite importar todos los schemas desde un solo lugar:
    from app.schemas import RegisterRequest, LoginRequest, TripRequest, etc.

En lugar de importar de cada archivo individualmente:
    from app.schemas.auth import RegisterRequest
    from app.schemas.trip import TripRequest
"""

from app.schemas.base import (
    EspinarGoBaseModel,
    MessageResponse,
    ErrorResponse,
    PaginationMeta,
    validate_peru_phone,
    validate_password_strength,
    validate_price,
    validate_score,
)

from app.schemas.auth import (
    RegisterRequest,
    RegisterResponse,
    SendOTPRequest,
    SendOTPResponse,
    VerifyOTPRequest,
    VerifyOTPResponse,
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    ChangePasswordRequest,
    ResetPasswordRequest,
)

from app.schemas.user import (
    UserPublicOut,
    UserProfile,
    UpdateProfileRequest,
    UpdateAvatarResponse,
    DriverProfilePublic,
    UpdateVehicleRequest,
    UploadDocumentResponse,
)

from app.schemas.trip import (
    TripRequest,
    TripPublic,
    TripOfferRequest,
    TripOfferPublic,
    AcceptOfferRequest,
    UpdateTripStatusRequest,
    TripListResponse,
)

from app.schemas.package import (
    PackageRequest,
    PackagePublic,
    PackageTrackingEvent,
    PackageTrackingResponse,
    PackageListResponse,
)

from app.schemas.rating import (
    RatingRequest,
    RatingPublic,
    RatingSummary,
)

__all__ = [
    # Base
    "EspinarGoBaseModel",
    "MessageResponse",
    "ErrorResponse",
    "PaginationMeta",
    "validate_peru_phone",
    "validate_password_strength",
    "validate_price",
    "validate_score",
    # Auth
    "RegisterRequest",
    "RegisterResponse",
    "SendOTPRequest",
    "SendOTPResponse",
    "VerifyOTPRequest",
    "VerifyOTPResponse",
    "LoginRequest",
    "TokenResponse",
    "RefreshTokenRequest",
    "RefreshTokenResponse",
    "ChangePasswordRequest",
    "ResetPasswordRequest",
    # User
    "UserPublicOut",
    "UserProfile",
    "UpdateProfileRequest",
    "UpdateAvatarResponse",
    "DriverProfilePublic",
    "UpdateVehicleRequest",
    "UploadDocumentResponse",
    # Trip
    "TripRequest",
    "TripPublic",
    "TripOfferRequest",
    "TripOfferPublic",
    "AcceptOfferRequest",
    "UpdateTripStatusRequest",
    "TripListResponse",
    # Package
    "PackageRequest",
    "PackagePublic",
    "PackageTrackingEvent",
    "PackageTrackingResponse",
    "PackageListResponse",
    # Rating
    "RatingRequest",
    "RatingPublic",
    "RatingSummary",
]