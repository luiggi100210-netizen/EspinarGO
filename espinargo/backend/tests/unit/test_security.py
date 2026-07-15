"""
Tests unitarios para app/core/security.py.

Verifica el comportamiento de las funciones criptográficas puras:
hashing de contraseñas, creación/decodificación de JWT, generación
de tokens y OTP, y enmascaramiento de teléfonos.

No requiere base de datos ni servicios externos.
"""

import re
from datetime import timedelta, timezone, datetime

import pytest
import jwt
from jwt.exceptions import PyJWTError as JWTError
from uuid import UUID

from app.core.config import settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_otp_code,
    generate_refresh_token,
    get_otp_expiry,
    get_refresh_token_expiry,
    hash_password,
    mask_phone_number,
    verify_password,
)

_FAKE_UUID = UUID("12345678-1234-5678-1234-567812345678")


# =============================================================================
# hash_password / verify_password
# =============================================================================


class TestPasswordHashing:

    def test_hash_is_not_plain_text(self):
        hashed = hash_password("secreto")
        assert hashed != "secreto"

    def test_hash_starts_with_bcrypt_prefix(self):
        hashed = hash_password("mi_clave")
        assert hashed.startswith("$2b$")

    def test_same_password_produces_different_hashes(self):
        h1 = hash_password("igual")
        h2 = hash_password("igual")
        assert h1 != h2, "bcrypt debe incluir salt aleatorio"

    def test_verify_correct_password_returns_true(self):
        hashed = hash_password("mi_clave")
        assert verify_password("mi_clave", hashed) is True

    def test_verify_wrong_password_returns_false(self):
        hashed = hash_password("mi_clave")
        assert verify_password("clave_incorrecta", hashed) is False

    def test_verify_empty_string_against_hash(self):
        hashed = hash_password("no_vacio")
        assert verify_password("", hashed) is False

    def test_hash_long_password(self):
        long_pass = "a" * 128
        hashed = hash_password(long_pass)
        assert verify_password(long_pass, hashed) is True


# =============================================================================
# create_access_token / decode_access_token
# =============================================================================


class TestJWT:

    def _make_token(self, **kwargs) -> str:
        defaults = dict(
            user_id=_FAKE_UUID,
            role="passenger",
            phone_number="+51987654321",
        )
        defaults.update(kwargs)
        return create_access_token(**defaults)

    def test_token_is_string(self):
        token = self._make_token()
        assert isinstance(token, str)
        assert len(token) > 50

    def test_token_has_three_parts(self):
        token = self._make_token()
        parts = token.split(".")
        assert len(parts) == 3

    def test_decode_returns_correct_subject(self):
        token = self._make_token()
        payload = decode_access_token(token)
        assert payload["sub"] == str(_FAKE_UUID)

    def test_decode_returns_correct_role(self):
        token = self._make_token(role="driver")
        payload = decode_access_token(token)
        assert payload["role"] == "driver"

    def test_decode_returns_correct_phone(self):
        token = self._make_token(phone_number="+51987654321")
        payload = decode_access_token(token)
        assert payload["phone"] == "+51987654321"

    def test_token_type_is_access(self):
        token = self._make_token()
        payload = decode_access_token(token)
        assert payload["type"] == "access"

    def test_decode_invalid_token_raises(self):
        with pytest.raises(JWTError):
            decode_access_token("not.a.valid.token")

    def test_decode_tampered_token_raises(self):
        token = self._make_token()
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(JWTError):
            decode_access_token(tampered)

    def test_decode_expired_token_raises(self):
        expired_token = create_access_token(
            user_id=_FAKE_UUID,
            role="passenger",
            phone_number="+51987654321",
            expires_delta=timedelta(seconds=-1),
        )
        with pytest.raises(JWTError):
            decode_access_token(expired_token)

    def test_refresh_token_rejected_as_access(self):
        """Un token con type='refresh' no debe ser aceptado como access."""
        payload = {
            "sub": str(_FAKE_UUID),
            "role": "passenger",
            "phone": "+51987654321",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(days=30),
            "type": "refresh",
        }
        refresh_jwt = jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
        with pytest.raises(JWTError):
            decode_access_token(refresh_jwt)

    def test_custom_expiry_delta(self):
        token = create_access_token(
            user_id=_FAKE_UUID,
            role="admin",
            phone_number="+51987654321",
            expires_delta=timedelta(hours=1),
        )
        payload = decode_access_token(token)
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        diff = (exp - now).total_seconds()
        assert 3500 < diff < 3700


# =============================================================================
# generate_refresh_token
# =============================================================================


class TestRefreshToken:

    def test_token_is_128_hex_chars(self):
        token = generate_refresh_token()
        assert len(token) == 128
        assert re.fullmatch(r"[0-9a-f]+", token)

    def test_tokens_are_unique(self):
        tokens = {generate_refresh_token() for _ in range(10)}
        assert len(tokens) == 10

    def test_get_refresh_token_expiry_is_future(self):
        expiry = get_refresh_token_expiry()
        now = datetime.now(timezone.utc)
        assert expiry > now

    def test_refresh_expiry_approx_30_days(self):
        expiry = get_refresh_token_expiry()
        now = datetime.now(timezone.utc)
        diff_days = (expiry - now).days
        assert 29 <= diff_days <= 31


# =============================================================================
# generate_otp_code
# =============================================================================


class TestOTPCode:

    def test_dev_mode_always_returns_123456(self):
        """En DEVELOPMENT el código es siempre 123456."""
        assert settings.is_development
        assert generate_otp_code() == "123456"

    def test_otp_is_string(self):
        code = generate_otp_code()
        assert isinstance(code, str)

    def test_otp_length_6(self):
        code = generate_otp_code(length=6)
        assert len(code) == 6

    def test_get_otp_expiry_is_future(self):
        expiry = get_otp_expiry()
        now = datetime.now(timezone.utc)
        assert expiry > now

    def test_otp_expiry_approx_10_minutes(self):
        expiry = get_otp_expiry()
        now = datetime.now(timezone.utc)
        diff_seconds = (expiry - now).total_seconds()
        assert 550 < diff_seconds < 650


# =============================================================================
# mask_phone_number
# =============================================================================


class TestMaskPhoneNumber:

    def test_masks_peruvian_number(self):
        result = mask_phone_number("+51987654321")
        assert result == "+51 ****** 21"

    def test_last_two_digits_visible(self):
        result = mask_phone_number("+51900000099")
        assert result.endswith("99")

    def test_asterisks_present(self):
        result = mask_phone_number("+51987654321")
        assert "***" in result

    def test_short_number_returned_as_is(self):
        result = mask_phone_number("+1")
        assert result == "+1"

    def test_empty_string_returned_as_is(self):
        result = mask_phone_number("")
        assert result == ""
