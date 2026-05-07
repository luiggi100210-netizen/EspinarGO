"""
Tests de integración para registro, send-OTP, health check y perfil.

Cubre: validaciones de registro, send-otp edge cases, health check,
GET /auth/me para distintos roles, flujo de login/refresh edge cases.
"""

import pytest
from httpx import AsyncClient


_BASE_PASSENGER = {
    "full_name": "Test Pasajero",
    "phone_number": "+51900001000",
    "email": "base1000@test.com",
    "password": "pass1234",
    "role": "passenger",
}


class TestHealthCheck:

    async def test_health_returns_ok(self, client: AsyncClient):
        """El health check retorna status ok."""
        resp = await client.get("/api/v1/auth/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "module" in data

    async def test_health_is_public(self, client: AsyncClient):
        """El health check no requiere autenticación."""
        resp = await client.get("/api/v1/auth/health")
        assert resp.status_code == 200


class TestRegisterValidation:

    async def test_missing_full_name_returns_422(self, client: AsyncClient):
        data = {k: v for k, v in _BASE_PASSENGER.items() if k != "full_name"}
        data["phone_number"] = "+51900001010"
        data["email"] = "miss1010@test.com"
        resp = await client.post("/api/v1/auth/register", json=data)
        assert resp.status_code == 422

    async def test_missing_password_returns_422(self, client: AsyncClient):
        data = {k: v for k, v in _BASE_PASSENGER.items() if k != "password"}
        data["phone_number"] = "+51900001011"
        data["email"] = "miss1011@test.com"
        resp = await client.post("/api/v1/auth/register", json=data)
        assert resp.status_code == 422

    async def test_missing_phone_returns_422(self, client: AsyncClient):
        data = {k: v for k, v in _BASE_PASSENGER.items() if k != "phone_number"}
        data["email"] = "miss1012@test.com"
        resp = await client.post("/api/v1/auth/register", json=data)
        assert resp.status_code == 422

    async def test_invalid_phone_format_returns_422(self, client: AsyncClient):
        """Formato de teléfono inválido → 422."""
        resp = await client.post(
            "/api/v1/auth/register",
            json={**_BASE_PASSENGER, "phone_number": "no-es-telefono", "email": "inv1013@test.com"},
        )
        assert resp.status_code == 422

    async def test_invalid_role_returns_422(self, client: AsyncClient):
        """Rol inexistente → 422."""
        resp = await client.post(
            "/api/v1/auth/register",
            json={**_BASE_PASSENGER, "role": "superadmin", "phone_number": "+51900001014", "email": "inv1014@test.com"},
        )
        assert resp.status_code == 422

    async def test_short_password_returns_422(self, client: AsyncClient):
        """Contraseña muy corta → 422."""
        resp = await client.post(
            "/api/v1/auth/register",
            json={**_BASE_PASSENGER, "password": "abc", "phone_number": "+51900001015", "email": "short1015@test.com"},
        )
        assert resp.status_code == 422

    async def test_duplicate_phone_returns_400(self, client: AsyncClient):
        """Número de teléfono ya registrado → 400."""
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Duplicado",
                "phone_number": "+51900000001",  # ya existe en conftest
                "email": "dup1000@test.com",
                "password": "pass1234",
                "role": "passenger",
            },
        )
        assert resp.status_code == 400

    async def test_register_passenger_returns_201(self, client: AsyncClient):
        """Registro válido de pasajero → 201."""
        resp = await client.post(
            "/api/v1/auth/register",
            json={**_BASE_PASSENGER, "phone_number": "+51900001020", "email": "psg1020@test.com"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["next_step"] == "verify_phone"
        assert "user_id" in data
        assert data["phone_number"] == "+51900001020"

    async def test_register_driver_returns_201(self, client: AsyncClient):
        """Registro válido de conductor → 201."""
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Conductor Nuevo",
                "phone_number": "+51900001021",
                "email": "drv1021@test.com",
                "password": "pass1234",
                "role": "driver",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "user_id" in data

    async def test_register_response_has_expected_fields(self, client: AsyncClient):
        """La respuesta de registro tiene todos los campos del schema."""
        resp = await client.post(
            "/api/v1/auth/register",
            json={**_BASE_PASSENGER, "phone_number": "+51900001022", "email": "schema1022@test.com"},
        )
        assert resp.status_code == 201
        data = resp.json()
        for field in ["user_id", "phone_number", "next_step", "message"]:
            assert field in data, f"Campo faltante: {field}"


class TestSendOTPEdgeCases:

    async def test_unknown_phone_returns_404(self, client: AsyncClient):
        """Teléfono no registrado → 404 (no requiere Redis)."""
        resp = await client.post(
            "/api/v1/auth/send-otp",
            json={"phone_number": "+51999888000"},
        )
        assert resp.status_code == 404

    async def test_invalid_phone_format_returns_422(self, client: AsyncClient):
        """Formato de teléfono inválido → 422."""
        resp = await client.post(
            "/api/v1/auth/send-otp",
            json={"phone_number": "no-telefono"},
        )
        assert resp.status_code == 422

    async def test_missing_phone_returns_422(self, client: AsyncClient):
        """Payload vacío → 422."""
        resp = await client.post("/api/v1/auth/send-otp", json={})
        assert resp.status_code == 422


class TestGetMyProfile:

    async def test_requires_auth(self, client: AsyncClient):
        """Sin token → 401."""
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    async def test_passenger_profile_has_expected_fields(
        self, client: AsyncClient, passenger_token: str
    ):
        """El perfil del pasajero contiene los campos esperados."""
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        for field in ["id", "full_name", "phone_number", "role", "phone_verified"]:
            assert field in data, f"Campo faltante: {field}"

    async def test_driver_profile_shows_driver_role(
        self, client: AsyncClient, driver_token: str
    ):
        """El perfil del conductor indica su rol."""
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["role"] == "driver"

    async def test_admin_profile_shows_admin_role(
        self, client: AsyncClient, admin_token: str
    ):
        """El perfil del admin indica su rol."""
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["role"] == "admin"

    async def test_profile_does_not_expose_password(
        self, client: AsyncClient, passenger_token: str
    ):
        """El perfil no expone el hash de contraseña."""
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "password" not in data
        assert "password_hash" not in data


class TestLoginEdgeCases:

    async def test_wrong_password_returns_401(self, client: AsyncClient):
        """Contraseña incorrecta → 401."""
        resp = await client.post(
            "/api/v1/auth/login",
            json={"phone_number": "+51900000001", "password": "wrongpassword"},
        )
        assert resp.status_code == 401

    async def test_unknown_phone_returns_401(self, client: AsyncClient):
        """Teléfono no registrado → 401."""
        resp = await client.post(
            "/api/v1/auth/login",
            json={"phone_number": "+51999000000", "password": "pass1234"},
        )
        assert resp.status_code == 401

    async def test_missing_password_returns_422(self, client: AsyncClient):
        """Payload sin password → 422."""
        resp = await client.post(
            "/api/v1/auth/login",
            json={"phone_number": "+51900000001"},
        )
        assert resp.status_code == 422

    async def test_missing_phone_returns_422(self, client: AsyncClient):
        """Payload sin phone_number → 422."""
        resp = await client.post(
            "/api/v1/auth/login",
            json={"password": "pass1234"},
        )
        assert resp.status_code == 422

    async def test_login_response_has_expected_fields(self, client: AsyncClient):
        """Login exitoso retorna todos los campos del token."""
        resp = await client.post(
            "/api/v1/auth/login",
            json={"phone_number": "+51900000001", "password": "pass1234"},
        )
        assert resp.status_code == 200
        data = resp.json()
        for field in ["access_token", "refresh_token", "token_type", "expires_in", "user"]:
            assert field in data, f"Campo faltante: {field}"
        assert data["token_type"] == "bearer"


class TestRefreshTokenEdgeCases:

    async def test_invalid_refresh_token_returns_401(self, client: AsyncClient):
        """Token de refresco inválido → 401."""
        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "token-que-no-existe-en-db"},
        )
        assert resp.status_code == 401

    async def test_missing_refresh_token_returns_422(self, client: AsyncClient):
        """Payload sin refresh_token → 422."""
        resp = await client.post("/api/v1/auth/refresh", json={})
        assert resp.status_code == 422

    async def test_valid_login_then_refresh(self, client: AsyncClient):
        """Login → refresh retorna nuevo access token."""
        login = await client.post(
            "/api/v1/auth/login",
            json={"phone_number": "+51900000001", "password": "pass1234"},
        )
        assert login.status_code == 200
        refresh_token = login.json()["refresh_token"]

        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
