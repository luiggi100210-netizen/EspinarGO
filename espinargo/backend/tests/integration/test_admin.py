"""
Tests de integración para el panel de administración.

Cubre /api/v1/admin/ (usuarios, conductores, stats).
Requiere el fixture admin_token definido en conftest.py.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from tests.integration.conftest import TestSession
from app.models.user import DriverStatus, User, UserStatus


class TestAdminAccess:

    async def test_non_admin_cannot_access_users(self, client: AsyncClient, passenger_token: str):
        resp = await client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 403

    async def test_driver_cannot_access_admin(self, client: AsyncClient, driver_token: str):
        resp = await client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 403

    async def test_unauthenticated_cannot_access_admin(self, client: AsyncClient):
        resp = await client.get("/api/v1/admin/users")
        assert resp.status_code == 401


class TestAdminListUsers:

    async def test_list_users_returns_paginated_response(
        self, client: AsyncClient, admin_token: str, passenger_token: str
    ):
        resp = await client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "users" in data
        assert "meta" in data
        assert data["meta"]["total"] >= 1

    async def test_filter_by_role_passenger(
        self, client: AsyncClient, admin_token: str, passenger_token: str
    ):
        resp = await client.get(
            "/api/v1/admin/users?role=passenger",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        users = resp.json()["users"]
        for user in users:
            assert user["role"] == "passenger"

    async def test_filter_by_role_driver(
        self, client: AsyncClient, admin_token: str, driver_token: str
    ):
        resp = await client.get(
            "/api/v1/admin/users?role=driver",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        users = resp.json()["users"]
        for user in users:
            assert user["role"] == "driver"

    async def test_filter_by_invalid_role_returns_400(
        self, client: AsyncClient, admin_token: str
    ):
        resp = await client.get(
            "/api/v1/admin/users?role=superadmin",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 400

    async def test_search_by_name(
        self, client: AsyncClient, admin_token: str, passenger_token: str
    ):
        resp = await client.get(
            "/api/v1/admin/users?search=Pasajero",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["meta"]["total"] >= 1

    async def test_search_no_results(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/admin/users?search=UsuarioQueNoExisteXYZ",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["meta"]["total"] == 0

    async def test_pagination(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/admin/users?page=1&per_page=1",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert len(resp.json()["users"]) <= 1


class TestAdminUserActions:

    async def _get_passenger_id(self) -> str:
        async with TestSession() as db:
            result = await db.execute(
                select(User).where(User.phone_number == "+51900000001")
            )
            user = result.scalar_one()
            return str(user.id)

    async def test_suspend_user(self, client: AsyncClient, admin_token: str, passenger_token: str):
        user_id = await self._get_passenger_id()

        resp = await client.post(
            f"/api/v1/admin/users/{user_id}/suspend",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert "suspendido" in resp.json()["message"].lower()

        # Reactivar para no romper otros tests
        await client.post(
            f"/api/v1/admin/users/{user_id}/activate",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

    async def test_ban_user(self, client: AsyncClient, admin_token: str, passenger_token: str):
        user_id = await self._get_passenger_id()

        resp = await client.post(
            f"/api/v1/admin/users/{user_id}/ban",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert "baneado" in resp.json()["message"].lower()

        # Reactivar para no romper otros tests
        await client.post(
            f"/api/v1/admin/users/{user_id}/activate",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

    async def test_activate_user(self, client: AsyncClient, admin_token: str, passenger_token: str):
        user_id = await self._get_passenger_id()

        await client.post(
            f"/api/v1/admin/users/{user_id}/suspend",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        resp = await client.post(
            f"/api/v1/admin/users/{user_id}/activate",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert "activado" in resp.json()["message"].lower()

    async def test_cannot_suspend_nonexistent_user(self, client: AsyncClient, admin_token: str):
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.post(
            f"/api/v1/admin/users/{fake_id}/suspend",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 404

    async def test_admin_cannot_suspend_themselves(self, client: AsyncClient, admin_token: str):
        async with TestSession() as db:
            result = await db.execute(
                select(User).where(User.phone_number == "+51900000003")
            )
            admin = result.scalar_one()
            admin_id = str(admin.id)

        resp = await client.post(
            f"/api/v1/admin/users/{admin_id}/suspend",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 400

    async def test_admin_cannot_ban_themselves(self, client: AsyncClient, admin_token: str):
        async with TestSession() as db:
            result = await db.execute(
                select(User).where(User.phone_number == "+51900000003")
            )
            admin = result.scalar_one()
            admin_id = str(admin.id)

        resp = await client.post(
            f"/api/v1/admin/users/{admin_id}/ban",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 400


class TestAdminDrivers:

    async def test_list_drivers(
        self, client: AsyncClient, admin_token: str, driver_token: str
    ):
        resp = await client.get(
            "/api/v1/admin/drivers",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "drivers" in data
        assert "meta" in data
        assert data["meta"]["total"] >= 1

    async def test_filter_drivers_by_status_approved(
        self, client: AsyncClient, admin_token: str, driver_token: str
    ):
        resp = await client.get(
            "/api/v1/admin/drivers?driver_status=approved",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        drivers = resp.json()["drivers"]
        for d in drivers:
            assert d["driver_profile"]["driver_status"] == "approved"

    async def test_filter_drivers_invalid_status(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/admin/drivers?driver_status=invalid_status",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 400

    async def test_review_driver_approve(self, client: AsyncClient, admin_token: str):
        """Crea un conductor en estado under_review y lo aprueba."""
        async with TestSession() as db:
            from app.models.user import DriverProfile, DriverStatus, UserRole, UserStatus
            from app.core.security import hash_password

            result = await db.execute(
                select(User).where(User.phone_number == "+51900000010")
            )
            existing = result.scalar_one_or_none()

            if not existing:
                driver_user = User(
                    full_name="Conductor Review",
                    phone_number="+51900000010",
                    email="review@test.com",
                    hashed_password=hash_password("pass1234"),
                    role=UserRole.DRIVER,
                    status=UserStatus.ACTIVE,
                    phone_verified=True,
                )
                db.add(driver_user)
                await db.flush()

                dp = DriverProfile(
                    user_id=driver_user.id,
                    driver_status=DriverStatus.UNDER_REVIEW,
                )
                db.add(dp)
                await db.commit()
                await db.refresh(driver_user)
                driver_id = str(driver_user.id)
            else:
                from app.models.user import DriverProfile, DriverStatus
                result2 = await db.execute(
                    select(DriverProfile).where(DriverProfile.user_id == existing.id)
                )
                dp = result2.scalar_one()
                dp.driver_status = DriverStatus.UNDER_REVIEW
                await db.commit()
                driver_id = str(existing.id)

        resp = await client.post(
            f"/api/v1/admin/drivers/{driver_id}/review",
            json={"action": "approve"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert "aprobado" in resp.json()["message"].lower()

    async def test_review_driver_reject_requires_reason(self, client: AsyncClient, admin_token: str):
        """Rechazar sin motivo debe fallar."""
        async with TestSession() as db:
            from app.models.user import DriverProfile, DriverStatus, UserRole, UserStatus
            from app.core.security import hash_password

            result = await db.execute(
                select(User).where(User.phone_number == "+51900000011")
            )
            existing = result.scalar_one_or_none()

            if not existing:
                driver_user = User(
                    full_name="Conductor Reject",
                    phone_number="+51900000011",
                    email="reject@test.com",
                    hashed_password=hash_password("pass1234"),
                    role=UserRole.DRIVER,
                    status=UserStatus.ACTIVE,
                    phone_verified=True,
                )
                db.add(driver_user)
                await db.flush()
                dp = DriverProfile(
                    user_id=driver_user.id,
                    driver_status=DriverStatus.UNDER_REVIEW,
                )
                db.add(dp)
                await db.commit()
                await db.refresh(driver_user)
                driver_id = str(driver_user.id)
            else:
                from app.models.user import DriverProfile, DriverStatus
                result2 = await db.execute(
                    select(DriverProfile).where(DriverProfile.user_id == existing.id)
                )
                dp = result2.scalar_one()
                dp.driver_status = DriverStatus.UNDER_REVIEW
                await db.commit()
                driver_id = str(existing.id)

        resp = await client.post(
            f"/api/v1/admin/drivers/{driver_id}/review",
            json={"action": "reject"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 400

    async def test_review_driver_reject_with_reason(self, client: AsyncClient, admin_token: str):
        """Rechazar con motivo debe funcionar correctamente."""
        async with TestSession() as db:
            from app.models.user import DriverProfile, DriverStatus, UserRole, UserStatus
            from app.core.security import hash_password

            result = await db.execute(
                select(User).where(User.phone_number == "+51900000012")
            )
            existing = result.scalar_one_or_none()

            if not existing:
                driver_user = User(
                    full_name="Conductor Reject2",
                    phone_number="+51900000012",
                    email="reject2@test.com",
                    hashed_password=hash_password("pass1234"),
                    role=UserRole.DRIVER,
                    status=UserStatus.ACTIVE,
                    phone_verified=True,
                )
                db.add(driver_user)
                await db.flush()
                dp = DriverProfile(
                    user_id=driver_user.id,
                    driver_status=DriverStatus.UNDER_REVIEW,
                )
                db.add(dp)
                await db.commit()
                await db.refresh(driver_user)
                driver_id = str(driver_user.id)
            else:
                from app.models.user import DriverProfile, DriverStatus
                result2 = await db.execute(
                    select(DriverProfile).where(DriverProfile.user_id == existing.id)
                )
                dp = result2.scalar_one()
                dp.driver_status = DriverStatus.UNDER_REVIEW
                await db.commit()
                driver_id = str(existing.id)

        resp = await client.post(
            f"/api/v1/admin/drivers/{driver_id}/review",
            json={"action": "reject", "rejection_reason": "Documentos ilegibles"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert "rechazado" in resp.json()["message"].lower()

    async def test_cannot_review_approved_driver(
        self, client: AsyncClient, admin_token: str, driver_token: str
    ):
        """No se puede revisar un conductor ya aprobado."""
        async with TestSession() as db:
            result = await db.execute(
                select(User).where(User.phone_number == "+51900000002")
            )
            driver = result.scalar_one()
            driver_id = str(driver.id)

        resp = await client.post(
            f"/api/v1/admin/drivers/{driver_id}/review",
            json={"action": "approve"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 400

    async def test_review_nonexistent_driver_returns_404(self, client: AsyncClient, admin_token: str):
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.post(
            f"/api/v1/admin/drivers/{fake_id}/review",
            json={"action": "approve"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 404


class TestAdminStats:

    async def test_stats_returns_all_fields(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/admin/stats",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        expected_fields = [
            "total_users", "active_users", "pending_users",
            "total_drivers", "approved_drivers", "pending_review_drivers",
            "total_trips", "completed_trips", "active_trips",
            "total_packages", "delivered_packages",
        ]
        for field in expected_fields:
            assert field in data, f"Campo '{field}' falta en la respuesta"

    async def test_stats_values_are_non_negative(
        self, client: AsyncClient, admin_token: str, passenger_token: str, driver_token: str
    ):
        resp = await client.get(
            "/api/v1/admin/stats",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        for key, value in data.items():
            assert value >= 0, f"'{key}' tiene valor negativo: {value}"

    async def test_stats_totals_consistent(
        self, client: AsyncClient, admin_token: str, passenger_token: str, driver_token: str
    ):
        """Los subtotales no pueden superar los totales."""
        resp = await client.get(
            "/api/v1/admin/stats",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        data = resp.json()
        assert data["active_users"] <= data["total_users"]
        assert data["approved_drivers"] <= data["total_drivers"]
        assert data["completed_trips"] <= data["total_trips"]
        assert data["delivered_packages"] <= data["total_packages"]

    async def test_stats_requires_admin(self, client: AsyncClient, passenger_token: str):
        resp = await client.get(
            "/api/v1/admin/stats",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 403
