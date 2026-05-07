"""
Tests de integración extendidos para el perfil de usuario.

Cubre: perfil de conductor no aprobado, actualización de email,
validaciones de vehículo, campos del perfil.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from tests.integration.conftest import TestSession
from app.core.security import hash_password
from app.models.user import DriverProfile, DriverStatus, User, UserRole, UserStatus


async def _create_pending_driver(phone: str, email: str) -> str:
    """Helper: crea un conductor en estado pending_docs, retorna su user_id."""
    async with TestSession() as db:
        result = await db.execute(select(User).where(User.phone_number == phone))
        existing = result.scalar_one_or_none()

        if existing:
            return str(existing.id)

        driver = User(
            full_name="Conductor Pendiente",
            phone_number=phone,
            email=email,
            password_hash=hash_password("pass1234"),
            role=UserRole.DRIVER,
            status=UserStatus.ACTIVE,
            phone_verified=True,
        )
        db.add(driver)
        await db.flush()

        dp = DriverProfile(
            user_id=driver.id,
            driver_status=DriverStatus.PENDING_DOCS,
        )
        db.add(dp)
        await db.commit()
        await db.refresh(driver)
        return str(driver.id)


class TestDriverProfileVisibility:

    async def test_non_approved_driver_not_visible(
        self, client: AsyncClient, passenger_token: str
    ):
        """Un conductor en estado pending_docs no es visible públicamente."""
        driver_id = await _create_pending_driver("+51900000060", "pending60@test.com")

        resp = await client.get(
            f"/api/v1/users/drivers/{driver_id}",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 404

    async def test_under_review_driver_not_visible(
        self, client: AsyncClient, passenger_token: str
    ):
        """Un conductor bajo revisión no es visible públicamente."""
        async with TestSession() as db:
            result = await db.execute(select(User).where(User.phone_number == "+51900000061"))
            existing = result.scalar_one_or_none()

            if not existing:
                driver = User(
                    full_name="Conductor En Revisión",
                    phone_number="+51900000061",
                    email="review61@test.com",
                    password_hash=hash_password("pass1234"),
                    role=UserRole.DRIVER,
                    status=UserStatus.ACTIVE,
                    phone_verified=True,
                )
                db.add(driver)
                await db.flush()
                dp = DriverProfile(user_id=driver.id, driver_status=DriverStatus.UNDER_REVIEW)
                db.add(dp)
                await db.commit()
                await db.refresh(driver)
                driver_id = str(driver.id)
            else:
                driver_id = str(existing.id)

        resp = await client.get(
            f"/api/v1/users/drivers/{driver_id}",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 404

    async def test_approved_driver_profile_has_expected_fields(
        self, client: AsyncClient, passenger_token: str
    ):
        """El perfil público del conductor aprobado tiene todos los campos esperados."""
        async with TestSession() as db:
            result = await db.execute(select(User).where(User.phone_number == "+51900000002"))
            driver = result.scalar_one()
            driver_id = str(driver.id)

        resp = await client.get(
            f"/api/v1/users/drivers/{driver_id}",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        for field in ["driver_status", "rating_display", "total_trips", "is_online"]:
            assert field in data, f"Campo faltante: {field}"


class TestUpdateProfileFields:

    async def test_update_multiple_fields_at_once(
        self, client: AsyncClient, passenger_token: str
    ):
        """Se pueden actualizar varios campos en una sola llamada."""
        resp = await client.patch(
            "/api/v1/users/me",
            json={"full_name": "Usuario Multi Update", "preferred_lang": "es"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["full_name"] == "Usuario Multi Update"
        assert data["preferred_lang"] == "es"

    async def test_update_profile_does_not_expose_password(
        self, client: AsyncClient, passenger_token: str
    ):
        """La respuesta del perfil no expone el hash de contraseña."""
        resp = await client.patch(
            "/api/v1/users/me",
            json={"full_name": "Seguro"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "password" not in data
        assert "password_hash" not in data

    async def test_profile_response_has_expected_schema(
        self, client: AsyncClient, passenger_token: str
    ):
        """La respuesta del perfil tiene todos los campos del schema."""
        resp = await client.patch(
            "/api/v1/users/me",
            json={},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        for field in ["id", "full_name", "phone_number", "role", "phone_verified", "preferred_lang"]:
            assert field in data, f"Campo faltante: {field}"


class TestUpdateVehicleFields:

    async def test_invalid_vehicle_type_rejected(
        self, client: AsyncClient, driver_token: str
    ):
        """Tipo de vehículo inválido es rechazado por validación."""
        resp = await client.patch(
            "/api/v1/users/me/vehicle",
            json={"vehicle_type": "helicóptero"},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 422

    async def test_invalid_vehicle_year_too_old_rejected(
        self, client: AsyncClient, driver_token: str
    ):
        """Año de vehículo anterior a 1990 es rechazado."""
        resp = await client.patch(
            "/api/v1/users/me/vehicle",
            json={"vehicle_year": 1985},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 422

    async def test_invalid_vehicle_year_future_rejected(
        self, client: AsyncClient, driver_token: str
    ):
        """Año de vehículo en el futuro es rechazado."""
        resp = await client.patch(
            "/api/v1/users/me/vehicle",
            json={"vehicle_year": 2099},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 422

    async def test_update_vehicle_seats(
        self, client: AsyncClient, driver_token: str
    ):
        """Se puede actualizar el número de asientos."""
        resp = await client.patch(
            "/api/v1/users/me/vehicle",
            json={"vehicle_seats": 4},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        # vehicle_seats se actualiza en DB pero DriverProfilePublic no lo expone
        assert resp.status_code == 200

    async def test_update_all_vehicle_fields(
        self, client: AsyncClient, driver_token: str
    ):
        """Actualizar varios campos del vehículo a la vez."""
        resp = await client.patch(
            "/api/v1/users/me/vehicle",
            json={
                "vehicle_brand": "Honda",
                "vehicle_model": "Wave Alpha",
                "vehicle_year": 2023,
                "vehicle_color": "Negro",
                "vehicle_plate": "XYZ-789",
                "vehicle_seats": 2,
            },
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["vehicle_brand"] == "Honda"
        assert data["vehicle_year"] == 2023
        assert data["vehicle_plate"] == "XYZ-789"

    async def test_vehicle_response_has_expected_fields(
        self, client: AsyncClient, driver_token: str
    ):
        """La respuesta de actualizar vehículo tiene los campos esperados."""
        resp = await client.patch(
            "/api/v1/users/me/vehicle",
            json={"vehicle_brand": "Yamaha"},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        for field in ["driver_status", "rating_display", "total_trips"]:
            assert field in data, f"Campo faltante: {field}"


class TestLoginStatusGuards:
    """Verifica que usuarios suspendidos/baneados no puedan autenticarse."""

    async def test_suspended_and_banned_users_cannot_login(
        self, client: AsyncClient, admin_token: str
    ):
        """Usuarios suspendidos y baneados no pueden hacer login."""
        # Crear ambos usuarios en un solo bloque de sesión
        async with TestSession() as db:
            # Usuario para suspensión
            result = await db.execute(select(User).where(User.phone_number == "+51900000070"))
            if not result.scalar_one_or_none():
                db.add(User(
                    full_name="Usuario Suspendido",
                    phone_number="+51900000070",
                    email="suspendido70@test.com",
                    password_hash=hash_password("pass1234"),
                    role=UserRole.PASSENGER,
                    status=UserStatus.ACTIVE,
                    phone_verified=True,
                ))

            # Usuario para ban
            result2 = await db.execute(select(User).where(User.phone_number == "+51900000071"))
            if not result2.scalar_one_or_none():
                db.add(User(
                    full_name="Usuario Baneado",
                    phone_number="+51900000071",
                    email="baneado71@test.com",
                    password_hash=hash_password("pass1234"),
                    role=UserRole.PASSENGER,
                    status=UserStatus.ACTIVE,
                    phone_verified=True,
                ))

            await db.commit()

            r1 = await db.execute(select(User).where(User.phone_number == "+51900000070"))
            suspended_id = str(r1.scalar_one().id)
            r2 = await db.execute(select(User).where(User.phone_number == "+51900000071"))
            banned_id = str(r2.scalar_one().id)

        # --- Test suspensión ---
        await client.post(
            f"/api/v1/admin/users/{suspended_id}/suspend",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        resp = await client.post(
            "/api/v1/auth/login",
            json={"phone_number": "+51900000070", "password": "pass1234"},
        )
        assert resp.status_code == 401

        await client.post(
            f"/api/v1/admin/users/{suspended_id}/activate",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # --- Test ban ---
        await client.post(
            f"/api/v1/admin/users/{banned_id}/ban",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        resp2 = await client.post(
            "/api/v1/auth/login",
            json={"phone_number": "+51900000071", "password": "pass1234"},
        )
        assert resp2.status_code == 401

        await client.post(
            f"/api/v1/admin/users/{banned_id}/activate",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
