"""
Tests de integración extendidos para autenticación.

Cubre: logout, logout-all, forgot-password, reset-password, change-password.
"""

import pytest
from httpx import AsyncClient


PASSENGER_PHONE = "+51900000001"
PASSENGER_PASSWORD = "pass1234"


async def _login(client: AsyncClient) -> dict:
    """Helper: hace login y retorna access_token y refresh_token."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"phone_number": PASSENGER_PHONE, "password": PASSENGER_PASSWORD},
    )
    assert resp.status_code == 200, f"Login failed: {resp.json()}"
    return resp.json()


class TestLogout:

    async def test_logout_requires_auth(self, client: AsyncClient):
        """Sin token de acceso → 401."""
        resp = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": "cualquier-token"},
        )
        assert resp.status_code == 401

    async def test_logout_success(self, client: AsyncClient, passenger_token: str):
        """Logout revoca el refresh token: el siguiente /refresh debe fallar."""
        tokens = await _login(client)
        access = tokens["access_token"]
        refresh = tokens["refresh_token"]

        logout_resp = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh},
            headers={"Authorization": f"Bearer {access}"},
        )
        assert logout_resp.status_code == 200

        # El refresh token ya no debe servir
        refresh_resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh},
        )
        assert refresh_resp.status_code == 401

    async def test_logout_nonexistent_token_is_ok(self, client: AsyncClient, passenger_token: str):
        """Logout con refresh token inexistente no genera error (idempotente)."""
        resp = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": "token-inexistente-xxxx"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200


class TestLogoutAll:

    async def test_logout_all_requires_auth(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/logout-all")
        assert resp.status_code == 401

    async def test_logout_all_success(self, client: AsyncClient, passenger_token: str):
        """Logout-all con token válido → 200."""
        resp = await client.post(
            "/api/v1/auth/logout-all",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200
        assert "message" in resp.json()


class TestForgotPassword:

    async def test_unknown_phone_returns_200(self, client: AsyncClient):
        """Número desconocido → 200 (respuesta genérica por seguridad)."""
        resp = await client.post(
            "/api/v1/auth/forgot-password",
            json={"phone_number": "+51999999998"},
        )
        assert resp.status_code == 200
        assert "mensaje" in resp.json().get("message", "").lower() or \
               resp.json().get("message") is not None

    async def test_invalid_phone_format_rejected(self, client: AsyncClient):
        """Formato inválido → 422."""
        resp = await client.post(
            "/api/v1/auth/forgot-password",
            json={"phone_number": "no-es-telefono"},
        )
        assert resp.status_code == 422


class TestResetPassword:

    async def test_wrong_otp_rejected(self, client: AsyncClient):
        """OTP incorrecto → 400."""
        resp = await client.post(
            "/api/v1/auth/reset-password",
            json={
                "phone_number": PASSENGER_PHONE,
                "otp_code": "000000",
                "new_password": "nuevaClave123",
            },
        )
        assert resp.status_code == 400



class TestChangePassword:

    async def test_change_password_requires_auth(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/change-password",
            json={"current_password": "pass1234", "new_password": "nueva1234"},
        )
        assert resp.status_code == 401

    async def test_wrong_current_password_rejected(self, client: AsyncClient, passenger_token: str):
        resp = await client.post(
            "/api/v1/auth/change-password",
            json={"current_password": "incorrecta", "new_password": "nueva1234"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 400
        assert "incorrecta" in resp.json()["detail"].lower()

    async def test_short_new_password_rejected(self, client: AsyncClient, passenger_token: str):
        resp = await client.post(
            "/api/v1/auth/change-password",
            json={"current_password": PASSENGER_PASSWORD, "new_password": "abc"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 422
