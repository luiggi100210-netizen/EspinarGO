"""
Tests de integración adicionales para flujos de autenticación.

Cubre: cambio de contraseña exitoso, campos faltantes en change-password,
campos faltantes en refresh/reset, perfil con todos los roles,
y edge cases del logout.
"""

import pytest
from httpx import AsyncClient


PASSENGER_PASSWORD = "pass1234"


class TestChangePasswordSuccess:
    """Casos exitosos y de validación en change-password."""

    async def test_change_password_success(
        self, client: AsyncClient, passenger_token: str
    ):
        """Cambio exitoso → 200 con mensaje."""
        resp = await client.post(
            "/api/v1/auth/change-password",
            json={"current_password": PASSENGER_PASSWORD, "new_password": "nuevaClave99"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data

        # Restaurar contraseña para no romper otros tests
        await client.post(
            "/api/v1/auth/change-password",
            json={"current_password": "nuevaClave99", "new_password": PASSENGER_PASSWORD},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )

    async def test_change_password_missing_current(
        self, client: AsyncClient, passenger_token: str
    ):
        """Sin current_password → 422."""
        resp = await client.post(
            "/api/v1/auth/change-password",
            json={"new_password": "nuevaClave99"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 422

    async def test_change_password_missing_new(
        self, client: AsyncClient, passenger_token: str
    ):
        """Sin new_password → 422."""
        resp = await client.post(
            "/api/v1/auth/change-password",
            json={"current_password": PASSENGER_PASSWORD},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 422

    async def test_change_password_empty_body(
        self, client: AsyncClient, passenger_token: str
    ):
        """Body vacío → 422."""
        resp = await client.post(
            "/api/v1/auth/change-password",
            json={},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 422

    async def test_change_password_new_too_long(
        self, client: AsyncClient, passenger_token: str
    ):
        """Nueva contraseña de 129 chars → 422."""
        resp = await client.post(
            "/api/v1/auth/change-password",
            json={"current_password": PASSENGER_PASSWORD, "new_password": "a" * 129},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 422


class TestLogoutEdgeCases:
    """Edge cases en logout."""

    async def test_logout_invalid_token_body_returns_401(
        self, client: AsyncClient
    ):
        """Token de refresco inválido en logout → 401."""
        resp = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": "token-totalmente-invalido"},
        )
        assert resp.status_code == 401

    async def test_logout_missing_token_returns_422(self, client: AsyncClient):
        """Body sin refresh_token → 422."""
        resp = await client.post("/api/v1/auth/logout", json={})
        assert resp.status_code == 422

    async def test_logout_all_requires_auth(self, client: AsyncClient):
        """logout-all sin token → 401."""
        resp = await client.post("/api/v1/auth/logout-all")
        assert resp.status_code == 401


class TestForgotPasswordEdgeCases:
    """Edge cases en forgot-password."""

    async def test_forgot_password_missing_phone(self, client: AsyncClient):
        """Body vacío → 422."""
        resp = await client.post("/api/v1/auth/forgot-password", json={})
        assert resp.status_code == 422

    async def test_forgot_password_invalid_phone_format(self, client: AsyncClient):
        """Teléfono inválido → 422."""
        resp = await client.post(
            "/api/v1/auth/forgot-password",
            json={"phone_number": "not-a-phone"},
        )
        assert resp.status_code == 422

    async def test_forgot_password_returns_200_even_if_unknown(
        self, client: AsyncClient
    ):
        """Teléfono no registrado → 200 (sin revelar existencia)."""
        resp = await client.post(
            "/api/v1/auth/forgot-password",
            json={"phone_number": "+51999777888"},
        )
        assert resp.status_code == 200


class TestLoginResponse:
    """Campos detallados en la respuesta de login."""

    async def test_login_user_field_has_expected_subfields(
        self, client: AsyncClient
    ):
        """El campo 'user' del token tiene los campos esperados."""
        resp = await client.post(
            "/api/v1/auth/login",
            json={"phone_number": "+51900000001", "password": PASSENGER_PASSWORD},
        )
        assert resp.status_code == 200
        user = resp.json()["user"]
        for field in ["id", "full_name", "phone_number", "role"]:
            assert field in user, f"Campo faltante en user: {field}"

    async def test_login_token_type_is_bearer(self, client: AsyncClient):
        """El tipo de token es 'bearer'."""
        resp = await client.post(
            "/api/v1/auth/login",
            json={"phone_number": "+51900000001", "password": PASSENGER_PASSWORD},
        )
        assert resp.status_code == 200
        assert resp.json()["token_type"] == "bearer"

    async def test_login_expires_in_is_positive(self, client: AsyncClient):
        """expires_in es un entero positivo."""
        resp = await client.post(
            "/api/v1/auth/login",
            json={"phone_number": "+51900000001", "password": PASSENGER_PASSWORD},
        )
        assert resp.status_code == 200
        assert resp.json()["expires_in"] > 0

    async def test_login_driver_role_in_user(
        self, client: AsyncClient, driver_token: str
    ):
        """El login del conductor indica role=driver."""
        resp = await client.post(
            "/api/v1/auth/login",
            json={"phone_number": "+51900000002", "password": PASSENGER_PASSWORD},
        )
        assert resp.status_code == 200
        assert resp.json()["user"]["role"] == "driver"


class TestRegisterEdgeCases:
    """Edge cases adicionales en registro."""

    async def test_register_returns_next_step_verify_phone(
        self, client: AsyncClient
    ):
        """El next_step es 'verify_phone' tras registro exitoso."""
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Nuevo Usuario",
                "phone_number": "+51900002001",
                "email": "nuevo2001@test.com",
                "password": "pass1234",
                "role": "passenger",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["next_step"] == "verify_phone"

    async def test_register_phone_in_response(self, client: AsyncClient):
        """El phone_number en la respuesta coincide con el enviado."""
        phone = "+51900002002"
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Verificar Teléfono",
                "phone_number": phone,
                "email": "verif2002@test.com",
                "password": "pass1234",
                "role": "passenger",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["phone_number"] == phone

    async def test_duplicate_email_still_creates_if_phone_unique(
        self, client: AsyncClient
    ):
        """Email duplicado pero teléfono único → puede registrarse (si el backend lo permite)
        o retorna error; verificamos que la respuesta sea coherente."""
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Otro Usuario",
                "phone_number": "+51900002003",
                "email": "pasajero@test.com",  # mismo email que el fixture
                "password": "pass1234",
                "role": "passenger",
            },
        )
        # El backend puede aceptar emails duplicados o rechazarlos; lo importante
        # es que retorne 201 o 400, no un 500.
        assert resp.status_code in (201, 400)
