"""
Tests unitarios para las propiedades y métodos de los modelos ORM.

Cubre: User.is_active/is_driver/is_passenger/is_admin/display_name,
RefreshToken.is_expired, DriverProfile.rating_display/is_approved.

Sin DB ni HTTP — instancia directa de los modelos.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from uuid import uuid4

import pytest

from app.models.user import (
    DriverProfile,
    DriverStatus,
    RefreshToken,
    User,
    UserRole,
    UserStatus,
)

# Las relationships de User referencian Trip, Rating y Package por nombre;
# hay que registrar esos modelos y configurar los mappers para poder
# instanciar los modelos sin base de datos.
import app.models.package  # noqa: E402, F401
import app.models.rating  # noqa: E402, F401
import app.models.trip  # noqa: E402, F401
from sqlalchemy.orm import configure_mappers

configure_mappers()


# =============================================================================
# Helpers
# =============================================================================

def _make_user(**kwargs) -> User:
    """Crea un User sin DB con los campos mínimos."""
    defaults = {
        "full_name": "Test User",
        "phone_number": "+51987654321",
        "role": UserRole.PASSENGER,
        "status": UserStatus.ACTIVE,
    }
    defaults.update(kwargs)
    return User(**defaults)


def _make_driver_profile(**kwargs) -> DriverProfile:
    """Crea un DriverProfile sin DB con los campos mínimos."""
    defaults = {
        "user_id": uuid4(),
        "driver_status": DriverStatus.APPROVED,
        "rating": 45,
        "rating_count": 10,
        "total_trips": 5,
        "is_online": False,
    }
    defaults.update(kwargs)
    return DriverProfile(**defaults)


def _make_refresh_token(expires_at: datetime) -> RefreshToken:
    """Crea un RefreshToken sin DB."""
    return RefreshToken(expires_at=expires_at, is_revoked=False)


# =============================================================================
# User.is_active
# =============================================================================


class TestUserIsActive:

    def test_active_user_returns_true(self):
        u = _make_user(status=UserStatus.ACTIVE)
        assert u.is_active is True

    def test_pending_user_returns_false(self):
        u = _make_user(status=UserStatus.PENDING)
        assert u.is_active is False

    def test_suspended_user_returns_false(self):
        u = _make_user(status=UserStatus.SUSPENDED)
        assert u.is_active is False

    def test_banned_user_returns_false(self):
        u = _make_user(status=UserStatus.BANNED)
        assert u.is_active is False


# =============================================================================
# User.is_driver / is_passenger / is_admin
# =============================================================================


class TestUserRoleProperties:

    def test_passenger_is_passenger(self):
        u = _make_user(role=UserRole.PASSENGER)
        assert u.is_passenger is True
        assert u.is_driver is False
        assert u.is_admin is False

    def test_driver_is_driver(self):
        u = _make_user(role=UserRole.DRIVER)
        assert u.is_driver is True
        assert u.is_passenger is False
        assert u.is_admin is False

    def test_admin_is_admin(self):
        u = _make_user(role=UserRole.ADMIN)
        assert u.is_admin is True
        assert u.is_driver is False
        assert u.is_passenger is False

    def test_passenger_not_admin(self):
        u = _make_user(role=UserRole.PASSENGER)
        assert u.is_admin is False

    def test_driver_not_passenger(self):
        u = _make_user(role=UserRole.DRIVER)
        assert u.is_passenger is False


# =============================================================================
# User.display_name
# =============================================================================


class TestUserDisplayName:

    def test_title_case_applied(self):
        u = _make_user(full_name="juan quispe mamani")
        assert u.display_name == "Juan Quispe Mamani"

    def test_already_title_case_unchanged(self):
        u = _make_user(full_name="Ana Torres")
        assert u.display_name == "Ana Torres"

    def test_all_uppercase_converted(self):
        u = _make_user(full_name="JUAN QUISPE")
        assert u.display_name == "Juan Quispe"

    def test_single_word_name(self):
        u = _make_user(full_name="maría")
        assert u.display_name == "María"

    def test_display_name_is_str(self):
        u = _make_user(full_name="Test Name")
        assert isinstance(u.display_name, str)


# =============================================================================
# RefreshToken.is_expired
# =============================================================================


class TestRefreshTokenIsExpired:

    def test_future_token_not_expired(self):
        future = datetime.now(timezone.utc) + timedelta(days=30)
        rt = _make_refresh_token(expires_at=future)
        assert rt.is_expired is False

    def test_past_token_is_expired(self):
        past = datetime.now(timezone.utc) - timedelta(seconds=1)
        rt = _make_refresh_token(expires_at=past)
        assert rt.is_expired is True

    def test_far_future_not_expired(self):
        far_future = datetime.now(timezone.utc) + timedelta(days=365)
        rt = _make_refresh_token(expires_at=far_future)
        assert rt.is_expired is False

    def test_long_past_expired(self):
        long_past = datetime.now(timezone.utc) - timedelta(days=60)
        rt = _make_refresh_token(expires_at=long_past)
        assert rt.is_expired is True


# =============================================================================
# DriverProfile.rating_display
# =============================================================================


class TestDriverProfileRatingDisplay:

    def test_rating_50_is_5_stars(self):
        """Rating interno 50 → 5.0 estrellas."""
        dp = _make_driver_profile(rating=50)
        assert dp.rating_display == 5.0

    def test_rating_0_is_0_stars(self):
        """Rating interno 0 → 0.0 estrellas."""
        dp = _make_driver_profile(rating=0)
        assert dp.rating_display == 0.0

    def test_rating_45_is_4_5_stars(self):
        """Rating interno 45 → 4.5 estrellas."""
        dp = _make_driver_profile(rating=45)
        assert dp.rating_display == 4.5

    def test_rating_48_is_4_8_stars(self):
        """Rating interno 48 → 4.8 estrellas."""
        dp = _make_driver_profile(rating=48)
        assert dp.rating_display == 4.8

    def test_rating_25_is_2_5_stars(self):
        """Rating interno 25 → 2.5 estrellas."""
        dp = _make_driver_profile(rating=25)
        assert dp.rating_display == 2.5

    def test_rating_display_is_float(self):
        """rating_display retorna un float."""
        dp = _make_driver_profile(rating=40)
        assert isinstance(dp.rating_display, float)

    def test_default_rating_50_yields_5_stars(self):
        """El rating por defecto (50) equivale a 5.0 estrellas."""
        dp = _make_driver_profile(rating=50)
        assert dp.rating_display == 5.0


# =============================================================================
# DriverProfile.is_approved
# =============================================================================


class TestDriverProfileIsApproved:

    def test_approved_driver_returns_true(self):
        dp = _make_driver_profile(driver_status=DriverStatus.APPROVED)
        assert dp.is_approved is True

    def test_pending_docs_returns_false(self):
        dp = _make_driver_profile(driver_status=DriverStatus.PENDING_DOCS)
        assert dp.is_approved is False

    def test_under_review_returns_false(self):
        dp = _make_driver_profile(driver_status=DriverStatus.UNDER_REVIEW)
        assert dp.is_approved is False

    def test_rejected_returns_false(self):
        dp = _make_driver_profile(driver_status=DriverStatus.REJECTED)
        assert dp.is_approved is False

    def test_suspended_returns_false(self):
        dp = _make_driver_profile(driver_status=DriverStatus.SUSPENDED)
        assert dp.is_approved is False

    def test_all_non_approved_statuses_return_false(self):
        """Todos los estados excepto APPROVED retornan False."""
        non_approved = [
            DriverStatus.PENDING_DOCS,
            DriverStatus.UNDER_REVIEW,
            DriverStatus.REJECTED,
            DriverStatus.SUSPENDED,
        ]
        for status in non_approved:
            dp = _make_driver_profile(driver_status=status)
            assert dp.is_approved is False, f"{status} debería retornar False"
