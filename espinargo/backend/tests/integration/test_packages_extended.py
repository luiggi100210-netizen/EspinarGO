"""
Tests de integración extendidos para encomiendas.

Cubre: guardias de autenticación/rol, listado de conductor,
transiciones de estado inválidas adicionales.
"""

import pytest
from httpx import AsyncClient


PACKAGE_DATA = {
    "recipient_name": "Pedro Quispe",
    "recipient_phone": "+51912345678",
    "delivery_address": "Av. Lima 456, Espinar",
    "size": "medium",
    "description": "Documentos importantes",
    "is_fragile": True,
    "payment_method": "cash",
}


async def _create_package(client: AsyncClient, passenger_token: str) -> str:
    resp = await client.post(
        "/api/v1/packages/",
        json=PACKAGE_DATA,
        headers={"Authorization": f"Bearer {passenger_token}"},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


class TestPackageAuth:
    """Guardias de autenticación y rol en encomiendas."""

    async def test_unauthenticated_cannot_create_package(self, client: AsyncClient):
        resp = await client.post("/api/v1/packages/", json=PACKAGE_DATA)
        assert resp.status_code == 401

    async def test_unauthenticated_cannot_get_my_packages(self, client: AsyncClient):
        resp = await client.get("/api/v1/packages/my")
        assert resp.status_code == 401

    async def test_driver_can_create_package(
        self, client: AsyncClient, driver_token: str
    ):
        """Cualquier usuario autenticado puede crear encomiendas."""
        resp = await client.post(
            "/api/v1/packages/",
            json=PACKAGE_DATA,
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["tracking_code"].startswith("ESP-")

    async def test_passenger_cannot_assign_package(
        self, client: AsyncClient, passenger_token: str
    ):
        """Solo conductores pueden auto-asignarse una encomienda."""
        pkg_id = await _create_package(client, passenger_token)

        resp = await client.post(
            f"/api/v1/packages/{pkg_id}/assign",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 403

    async def test_passenger_cannot_update_status(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Solo el conductor asignado puede actualizar el estado."""
        pkg_id = await _create_package(client, passenger_token)
        await client.post(
            f"/api/v1/packages/{pkg_id}/assign",
            headers={"Authorization": f"Bearer {driver_token}"},
        )

        resp = await client.post(
            f"/api/v1/packages/{pkg_id}/update-status",
            json={"status": "picked_up"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code in (403, 400)


class TestDriverPackages:
    """Tests para la perspectiva del conductor en encomiendas."""

    async def test_driver_gets_assigned_packages(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """El conductor puede ver sus encomiendas asignadas."""
        pkg_id = await _create_package(client, passenger_token)
        await client.post(
            f"/api/v1/packages/{pkg_id}/assign",
            headers={"Authorization": f"Bearer {driver_token}"},
        )

        resp = await client.get(
            "/api/v1/packages/my",
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["meta"]["total"] >= 1

    async def test_assign_nonexistent_package(
        self, client: AsyncClient, driver_token: str
    ):
        """Asignar encomienda inexistente → 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.post(
            f"/api/v1/packages/{fake_id}/assign",
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 404


class TestPackageStatusTransitions:
    """Transiciones de estado adicionales."""

    async def test_cannot_go_back_to_pending_from_assigned(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """No se puede retroceder al estado pending una vez asignado."""
        pkg_id = await _create_package(client, passenger_token)
        await client.post(
            f"/api/v1/packages/{pkg_id}/assign",
            headers={"Authorization": f"Bearer {driver_token}"},
        )

        resp = await client.post(
            f"/api/v1/packages/{pkg_id}/update-status",
            json={"status": "pending"},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        # "pending" es rechazado por validación (422) o lógica de negocio (400)
        assert resp.status_code in (400, 422)

    async def test_status_update_unauthenticated(
        self, client: AsyncClient, passenger_token: str
    ):
        """Sin token → 401."""
        pkg_id = await _create_package(client, passenger_token)
        resp = await client.post(
            f"/api/v1/packages/{pkg_id}/update-status",
            json={"status": "picked_up"},
        )
        assert resp.status_code == 401

    async def test_get_packages_pagination(
        self, client: AsyncClient, passenger_token: str
    ):
        """Paginación de listado de encomiendas."""
        resp = await client.get(
            "/api/v1/packages/my?page=1&per_page=5",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200
        meta = resp.json()["meta"]
        assert meta["page"] == 1
        assert meta["per_page"] == 5


class TestPackageCreation:
    """Validaciones al crear encomiendas."""

    async def test_envelope_size_accepted(
        self, client: AsyncClient, passenger_token: str
    ):
        """Tamaño 'envelope' es válido."""
        resp = await client.post(
            "/api/v1/packages/",
            json={**PACKAGE_DATA, "size": "envelope"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["size"] == "envelope"

    async def test_large_size_accepted(
        self, client: AsyncClient, passenger_token: str
    ):
        """Tamaño 'large' es válido."""
        resp = await client.post(
            "/api/v1/packages/",
            json={**PACKAGE_DATA, "size": "large"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 201

    async def test_missing_recipient_name_rejected(
        self, client: AsyncClient, passenger_token: str
    ):
        """Campo obligatorio faltante → 422."""
        data = {k: v for k, v in PACKAGE_DATA.items() if k != "recipient_name"}
        resp = await client.post(
            "/api/v1/packages/",
            json=data,
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 422
