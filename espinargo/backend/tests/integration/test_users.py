"""
Tests de integración para endpoints de perfil de usuario.

Cubre /api/v1/users/ (actualizar perfil, vehículo, ver conductor).
Los tests de subida de archivos (avatar, documentos) no se incluyen
porque requieren mocks de Cloudinary.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from tests.integration.conftest import TestSession
from app.models.user import User


class TestUpdateProfile:

    async def test_update_full_name(self, client: AsyncClient, passenger_token: str):
        resp = await client.patch(
            "/api/v1/users/me",
            json={"full_name": "Nuevo Nombre Test"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["full_name"] == "Nuevo Nombre Test"

    async def test_update_preferred_lang(self, client: AsyncClient, passenger_token: str):
        resp = await client.patch(
            "/api/v1/users/me",
            json={"preferred_lang": "en"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["preferred_lang"] == "en"

    async def test_update_profile_requires_auth(self, client: AsyncClient):
        resp = await client.patch(
            "/api/v1/users/me",
            json={"full_name": "Sin Token"},
        )
        assert resp.status_code == 401

    async def test_update_profile_returns_user_schema(self, client: AsyncClient, passenger_token: str):
        resp = await client.patch(
            "/api/v1/users/me",
            json={"full_name": "Test Schema"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert "phone_number" in data
        assert "role" in data

    async def test_empty_update_returns_current_profile(self, client: AsyncClient, passenger_token: str):
        """Enviar body vacío no rompe el endpoint."""
        resp = await client.patch(
            "/api/v1/users/me",
            json={},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200


class TestUpdateVehicle:

    async def test_driver_updates_vehicle(self, client: AsyncClient, driver_token: str):
        resp = await client.patch(
            "/api/v1/users/me/vehicle",
            json={
                "vehicle_brand": "Honda",
                "vehicle_model": "Wave",
                "vehicle_year": 2022,
                "vehicle_color": "Rojo",
                "vehicle_plate": "ABC-123",
            },
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["vehicle_brand"] == "Honda"
        assert data["vehicle_model"] == "Wave"

    async def test_passenger_cannot_update_vehicle(self, client: AsyncClient, passenger_token: str):
        resp = await client.patch(
            "/api/v1/users/me/vehicle",
            json={"vehicle_brand": "Toyota"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 403

    async def test_update_vehicle_requires_auth(self, client: AsyncClient):
        resp = await client.patch(
            "/api/v1/users/me/vehicle",
            json={"vehicle_brand": "Honda"},
        )
        assert resp.status_code == 401

    async def test_partial_vehicle_update(self, client: AsyncClient, driver_token: str):
        """Solo se actualizan los campos enviados."""
        await client.patch(
            "/api/v1/users/me/vehicle",
            json={"vehicle_brand": "Yamaha", "vehicle_color": "Azul"},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        resp = await client.patch(
            "/api/v1/users/me/vehicle",
            json={"vehicle_model": "Ray ZR"},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 200
        # El brand anterior se preserva
        assert resp.json()["vehicle_brand"] == "Yamaha"
        assert resp.json()["vehicle_model"] == "Ray ZR"


class TestGetDriverProfile:

    async def test_get_approved_driver_profile(self, client: AsyncClient, passenger_token: str, driver_token: str):
        """Un conductor aprobado puede ser visto por pasajeros."""
        async with TestSession() as db:
            result = await db.execute(
                select(User).where(User.phone_number == "+51900000002")
            )
            driver = result.scalar_one()
            driver_id = str(driver.id)

        resp = await client.get(
            f"/api/v1/users/drivers/{driver_id}",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["driver_status"] == "approved"
        assert "vehicle_type" in data
        assert "rating_display" in data

    async def test_driver_profile_requires_auth(self, client: AsyncClient, driver_token: str):
        async with TestSession() as db:
            result = await db.execute(
                select(User).where(User.phone_number == "+51900000002")
            )
            driver = result.scalar_one()
            driver_id = str(driver.id)

        resp = await client.get(f"/api/v1/users/drivers/{driver_id}")
        assert resp.status_code == 401

    async def test_nonexistent_driver_returns_404(self, client: AsyncClient, passenger_token: str):
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.get(
            f"/api/v1/users/drivers/{fake_id}",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 404
