"""
Tests de integración extendidos para el panel de administración.

Cubre: filtros por estado de usuario, búsqueda por teléfono,
filtros de conductor por estado, validaciones y casos borde.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from tests.integration.conftest import TestSession
from app.core.security import hash_password
from app.models.user import DriverProfile, DriverStatus, User, UserRole, UserStatus


async def _ensure_user(phone: str, email: str, role: UserRole = UserRole.PASSENGER) -> str:
    """Helper: obtiene o crea un usuario, retorna su user_id."""
    async with TestSession() as db:
        result = await db.execute(select(User).where(User.phone_number == phone))
        existing = result.scalar_one_or_none()
        if existing:
            return str(existing.id)

        user = User(
            full_name=f"Extended Test {phone[-4:]}",
            phone_number=phone,
            email=email,
            password_hash=hash_password("pass1234"),
            role=role,
            status=UserStatus.ACTIVE,
            phone_verified=True,
        )
        db.add(user)
        if role == UserRole.DRIVER:
            await db.flush()
            db.add(DriverProfile(user_id=user.id, driver_status=DriverStatus.PENDING_DOCS))
        await db.commit()
        await db.refresh(user)
        return str(user.id)


class TestAdminUserStatusFilter:
    """Filtros por estado en el listado de usuarios."""

    async def test_filter_active_users(self, client: AsyncClient, admin_token: str):
        """Solo retorna usuarios activos cuando se filtra por active."""
        resp = await client.get(
            "/api/v1/admin/users?status=active",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        users = resp.json()["users"]
        for user in users:
            assert user["status"] == "active"

    async def test_filter_suspended_users(self, client: AsyncClient, admin_token: str):
        """Solo retorna usuarios suspendidos cuando se filtra por suspended."""
        user_id = await _ensure_user("+51900000080", "ext80@test.com")
        await client.post(
            f"/api/v1/admin/users/{user_id}/suspend",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        resp = await client.get(
            "/api/v1/admin/users?status=suspended",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        users = resp.json()["users"]
        assert len(users) >= 1
        for user in users:
            assert user["status"] == "suspended"
        assert any(u["id"] == user_id for u in users)

        # Limpiar
        await client.post(
            f"/api/v1/admin/users/{user_id}/activate",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

    async def test_filter_banned_users(self, client: AsyncClient, admin_token: str):
        """Solo retorna usuarios baneados cuando se filtra por banned."""
        user_id = await _ensure_user("+51900000085", "ext85@test.com")
        await client.post(
            f"/api/v1/admin/users/{user_id}/ban",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        resp = await client.get(
            "/api/v1/admin/users?status=banned",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        users = resp.json()["users"]
        assert any(u["id"] == user_id for u in users)
        for user in users:
            assert user["status"] == "banned"

        # Limpiar
        await client.post(
            f"/api/v1/admin/users/{user_id}/activate",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

    async def test_filter_invalid_status_returns_400(
        self, client: AsyncClient, admin_token: str
    ):
        """Estado desconocido → 400."""
        resp = await client.get(
            "/api/v1/admin/users?status=desconocido",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 400

    async def test_filter_combined_role_and_status(
        self, client: AsyncClient, admin_token: str
    ):
        """Combinar filtros role y status funciona correctamente."""
        resp = await client.get(
            "/api/v1/admin/users?role=passenger&status=active",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        users = resp.json()["users"]
        for user in users:
            assert user["role"] == "passenger"
            assert user["status"] == "active"


class TestAdminUserSearch:
    """Búsqueda de usuarios por nombre y teléfono."""

    async def test_search_by_phone_number(self, client: AsyncClient, admin_token: str):
        """Buscar usuario por su número de teléfono exacto."""
        resp = await client.get(
            "/api/v1/admin/users?search=+51900000001",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["meta"]["total"] >= 1

    async def test_search_by_partial_phone(self, client: AsyncClient, admin_token: str):
        """Buscar por fragmento del teléfono."""
        resp = await client.get(
            "/api/v1/admin/users?search=9000000",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["meta"]["total"] >= 1

    async def test_search_no_results_returns_empty(
        self, client: AsyncClient, admin_token: str
    ):
        """Búsqueda sin resultados retorna lista vacía con total=0."""
        resp = await client.get(
            "/api/v1/admin/users?search=NumeroQueNuncaExistira99999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["meta"]["total"] == 0
        assert resp.json()["users"] == []

    async def test_search_combined_with_role(self, client: AsyncClient, admin_token: str):
        """Buscar por nombre combinado con filtro de rol."""
        resp = await client.get(
            "/api/v1/admin/users?role=driver&search=Conductor",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        users = resp.json()["users"]
        for user in users:
            assert user["role"] == "driver"


class TestAdminUserPagination:
    """Validaciones de paginación en el listado de usuarios."""

    async def test_per_page_above_max_rejected(self, client: AsyncClient, admin_token: str):
        """per_page > 100 es rechazado por validación (422)."""
        resp = await client.get(
            "/api/v1/admin/users?per_page=200",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 422

    async def test_page_zero_rejected(self, client: AsyncClient, admin_token: str):
        """page=0 es inválido (422)."""
        resp = await client.get(
            "/api/v1/admin/users?page=0",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 422

    async def test_pagination_meta_is_correct(self, client: AsyncClient, admin_token: str):
        """Los campos de meta coinciden con los parámetros solicitados."""
        resp = await client.get(
            "/api/v1/admin/users?page=2&per_page=1",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        meta = resp.json()["meta"]
        assert meta["page"] == 2
        assert meta["per_page"] == 1
        assert len(resp.json()["users"]) <= 1

    async def test_user_list_fields_are_complete(
        self, client: AsyncClient, admin_token: str
    ):
        """Cada usuario en la lista tiene los campos esperados."""
        resp = await client.get(
            "/api/v1/admin/users?per_page=1",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        users = resp.json()["users"]
        if users:
            for field in ["id", "full_name", "phone_number", "role", "status"]:
                assert field in users[0], f"Campo faltante en AdminUserOut: {field}"


class TestAdminDriverFilters:
    """Filtros por estado de conductor."""

    async def test_filter_pending_docs(self, client: AsyncClient, admin_token: str):
        """Filtrar conductores en estado pending_docs."""
        # Asegurar que existe al menos uno
        await _ensure_user("+51900000081", "drv81@test.com", role=UserRole.DRIVER)

        resp = await client.get(
            "/api/v1/admin/drivers?driver_status=pending_docs",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        drivers = resp.json()["drivers"]
        for d in drivers:
            assert d["driver_profile"]["driver_status"] == "pending_docs"

    async def test_filter_under_review(self, client: AsyncClient, admin_token: str):
        """Filtrar conductores bajo revisión retorna solo ese estado."""
        resp = await client.get(
            "/api/v1/admin/drivers?driver_status=under_review",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        drivers = resp.json()["drivers"]
        for d in drivers:
            assert d["driver_profile"]["driver_status"] == "under_review"

    async def test_filter_rejected(self, client: AsyncClient, admin_token: str):
        """Filtrar conductores rechazados retorna solo ese estado."""
        resp = await client.get(
            "/api/v1/admin/drivers?driver_status=rejected",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        drivers = resp.json()["drivers"]
        for d in drivers:
            assert d["driver_profile"]["driver_status"] == "rejected"

    async def test_driver_pagination_meta(self, client: AsyncClient, admin_token: str):
        """Paginación en lista de conductores tiene meta correcto."""
        resp = await client.get(
            "/api/v1/admin/drivers?page=1&per_page=2",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        meta = resp.json()["meta"]
        assert meta["page"] == 1
        assert meta["per_page"] == 2
        assert len(resp.json()["drivers"]) <= 2

    async def test_drivers_per_page_above_max_rejected(
        self, client: AsyncClient, admin_token: str
    ):
        """per_page > 100 en conductores es rechazado (422)."""
        resp = await client.get(
            "/api/v1/admin/drivers?per_page=200",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 422

    async def test_driver_list_has_profile_fields(
        self, client: AsyncClient, admin_token: str
    ):
        """Cada conductor en la lista tiene su driver_profile."""
        resp = await client.get(
            "/api/v1/admin/drivers?per_page=1",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        drivers = resp.json()["drivers"]
        if drivers:
            assert "driver_profile" in drivers[0]
            assert "driver_status" in drivers[0]["driver_profile"]


class TestAdminUserActionEdgeCases:
    """Casos borde en acciones administrativas sobre usuarios."""

    async def test_activate_nonexistent_user_returns_404(
        self, client: AsyncClient, admin_token: str
    ):
        """Activar usuario inexistente → 404."""
        resp = await client.post(
            "/api/v1/admin/users/00000000-0000-0000-0000-000000000099/activate",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 404

    async def test_ban_nonexistent_user_returns_404(
        self, client: AsyncClient, admin_token: str
    ):
        """Banear usuario inexistente → 404."""
        resp = await client.post(
            "/api/v1/admin/users/00000000-0000-0000-0000-000000000099/ban",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 404

    async def test_activate_already_active_is_idempotent(
        self, client: AsyncClient, admin_token: str
    ):
        """Activar un usuario ya activo no falla (idempotente)."""
        user_id = await _ensure_user("+51900000082", "idem82@test.com")
        resp = await client.post(
            f"/api/v1/admin/users/{user_id}/activate",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200

    async def test_suspend_then_ban_sequence(
        self, client: AsyncClient, admin_token: str
    ):
        """Suspender y luego banear un usuario funciona correctamente."""
        user_id = await _ensure_user("+51900000083", "seq83@test.com")

        await client.post(
            f"/api/v1/admin/users/{user_id}/suspend",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        resp = await client.post(
            f"/api/v1/admin/users/{user_id}/ban",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert "baneado" in resp.json()["message"].lower()

        # Limpiar
        await client.post(
            f"/api/v1/admin/users/{user_id}/activate",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

    async def test_suspend_requires_admin(
        self, client: AsyncClient, passenger_token: str
    ):
        """Suspender usuario sin rol admin → 403."""
        resp = await client.post(
            "/api/v1/admin/users/00000000-0000-0000-0000-000000000001/suspend",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 403


class TestAdminDriverReviewEdgeCases:
    """Casos borde en la revisión de conductores."""

    async def test_review_missing_action_returns_422(
        self, client: AsyncClient, admin_token: str
    ):
        """Payload sin campo action → 422."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.post(
            f"/api/v1/admin/drivers/{fake_id}/review",
            json={},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 422

    async def test_review_invalid_action_returns_400_or_422(
        self, client: AsyncClient, admin_token: str
    ):
        """Acción inválida en revisión → 400 o 422."""
        async with TestSession() as db:
            result = await db.execute(
                select(User).where(User.phone_number == "+51900000084")
            )
            existing = result.scalar_one_or_none()

        if existing:
            driver_id = str(existing.id)
        else:
            driver_id = await _ensure_user(
                "+51900000084", "drv84@test.com", role=UserRole.DRIVER
            )

        resp = await client.post(
            f"/api/v1/admin/drivers/{driver_id}/review",
            json={"action": "hold"},  # acción no válida
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code in (400, 422)

    async def test_review_requires_admin(
        self, client: AsyncClient, driver_token: str
    ):
        """Revisar conductor sin rol admin → 403."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.post(
            f"/api/v1/admin/drivers/{fake_id}/review",
            json={"action": "approve"},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 403


class TestAdminStatsExtended:
    """Casos extendidos para el endpoint de estadísticas."""

    async def test_stats_unauthenticated_returns_401(self, client: AsyncClient):
        """Sin token → 401."""
        resp = await client.get("/api/v1/admin/stats")
        assert resp.status_code == 401

    async def test_stats_driver_returns_403(
        self, client: AsyncClient, driver_token: str
    ):
        """Token de conductor → 403."""
        resp = await client.get(
            "/api/v1/admin/stats",
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 403

    async def test_stats_total_drivers_includes_pending(
        self, client: AsyncClient, admin_token: str
    ):
        """total_drivers incluye conductores en cualquier estado."""
        # Crear conductor pending_docs
        await _ensure_user("+51900000086", "drv86@test.com", role=UserRole.DRIVER)

        resp = await client.get(
            "/api/v1/admin/stats",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_drivers"] >= 1

    async def test_stats_pending_users_non_negative(
        self, client: AsyncClient, admin_token: str
    ):
        """pending_users siempre es >= 0."""
        resp = await client.get(
            "/api/v1/admin/stats",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.json()["pending_users"] >= 0

    async def test_stats_active_trips_non_negative(
        self, client: AsyncClient, admin_token: str
    ):
        """active_trips siempre es >= 0."""
        resp = await client.get(
            "/api/v1/admin/stats",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.json()["active_trips"] >= 0
