"""
Tests de integración para el listado de encomiendas propias y casos borde.

Cubre: paginación de /my (per_page>50, page=0), respuesta con meta,
encomienda recién creada aparece en listado, assign doble → 400.
"""

import pytest
from httpx import AsyncClient


PACKAGE_DATA = {
    "recipient_name": "Carlos Quispe",
    "recipient_phone": "+51987111222",
    "delivery_address": "Av. Circunvalación 456, Espinar",
    "size": "small",
    "description": "Libros",
    "is_fragile": False,
    "payment_method": "cash",
}


class TestMyPackagesPagination:
    """Validaciones de paginación del listado de encomiendas propias."""

    async def test_per_page_above_max_rejected(
        self, client: AsyncClient, passenger_token: str
    ):
        """per_page > 50 → 422."""
        resp = await client.get(
            "/api/v1/packages/my?per_page=51",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 422

    async def test_page_zero_rejected(
        self, client: AsyncClient, passenger_token: str
    ):
        """page=0 → 422 (mínimo es 1)."""
        resp = await client.get(
            "/api/v1/packages/my?page=0",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 422

    async def test_per_page_max_accepted(
        self, client: AsyncClient, passenger_token: str
    ):
        """per_page=50 (máximo) → 200."""
        resp = await client.get(
            "/api/v1/packages/my?per_page=50",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200

    async def test_response_has_packages_and_meta(
        self, client: AsyncClient, passenger_token: str
    ):
        """La respuesta incluye packages y meta."""
        resp = await client.get(
            "/api/v1/packages/my",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "packages" in data
        assert "meta" in data
        assert isinstance(data["packages"], list)

    async def test_meta_has_expected_fields(
        self, client: AsyncClient, passenger_token: str
    ):
        """Los campos de meta están presentes."""
        resp = await client.get(
            "/api/v1/packages/my",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200
        meta = resp.json()["meta"]
        for field in ["total", "page", "per_page", "total_pages", "has_next", "has_prev"]:
            assert field in meta, f"Campo faltante en meta: {field}"

    async def test_requires_auth(self, client: AsyncClient):
        """Sin token → 401."""
        resp = await client.get("/api/v1/packages/my")
        assert resp.status_code == 401

    async def test_created_package_appears_in_list(
        self, client: AsyncClient, passenger_token: str
    ):
        """Una encomienda recién creada aparece en el listado /my."""
        create = await client.post(
            "/api/v1/packages/",
            json=PACKAGE_DATA,
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert create.status_code == 201
        pkg_id = create.json()["id"]

        resp = await client.get(
            "/api/v1/packages/my",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200
        pkg_ids = [p["id"] for p in resp.json()["packages"]]
        assert pkg_id in pkg_ids

    async def test_driver_sees_own_packages_in_my(
        self, client: AsyncClient, driver_token: str
    ):
        """El conductor también puede listar sus encomiendas (rol activo)."""
        resp = await client.get(
            "/api/v1/packages/my",
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 200

    async def test_page_param_reflected_in_meta(
        self, client: AsyncClient, passenger_token: str
    ):
        """Los parámetros page y per_page se reflejan en meta."""
        resp = await client.get(
            "/api/v1/packages/my?page=1&per_page=10",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200
        meta = resp.json()["meta"]
        assert meta["page"] == 1
        assert meta["per_page"] == 10


class TestAssignPackageEdgeCases:
    """Casos borde al asignar encomiendas."""

    async def test_assign_already_assigned_package_returns_400(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Asignar una encomienda ya asignada → 400."""
        create = await client.post(
            "/api/v1/packages/",
            json=PACKAGE_DATA,
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert create.status_code == 201
        pkg_id = create.json()["id"]

        # Primera asignación
        first = await client.post(
            f"/api/v1/packages/{pkg_id}/assign",
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert first.status_code == 200

        # Segunda asignación
        second = await client.post(
            f"/api/v1/packages/{pkg_id}/assign",
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert second.status_code == 400

    async def test_assign_returns_assigned_status(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """La respuesta tras asignar muestra status=assigned."""
        create = await client.post(
            "/api/v1/packages/",
            json=PACKAGE_DATA,
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        pkg_id = create.json()["id"]

        resp = await client.post(
            f"/api/v1/packages/{pkg_id}/assign",
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "assigned"

    async def test_assign_requires_auth(
        self, client: AsyncClient, passenger_token: str
    ):
        """Sin token → 401 al asignar."""
        create = await client.post(
            "/api/v1/packages/",
            json=PACKAGE_DATA,
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        pkg_id = create.json()["id"]

        resp = await client.post(f"/api/v1/packages/{pkg_id}/assign")
        assert resp.status_code == 401

    async def test_passenger_cannot_assign_package(
        self, client: AsyncClient, passenger_token: str
    ):
        """Pasajero no puede asignarse encomiendas (solo conductores) → 403."""
        create = await client.post(
            "/api/v1/packages/",
            json=PACKAGE_DATA,
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        pkg_id = create.json()["id"]

        resp = await client.post(
            f"/api/v1/packages/{pkg_id}/assign",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 403

    async def test_package_response_has_tracking_code(
        self, client: AsyncClient, passenger_token: str
    ):
        """Una encomienda creada tiene tracking_code."""
        resp = await client.post(
            "/api/v1/packages/",
            json=PACKAGE_DATA,
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "tracking_code" in data
        assert data["tracking_code"].startswith("ESP-")

    async def test_package_response_has_status_pending(
        self, client: AsyncClient, passenger_token: str
    ):
        """Una encomienda recién creada tiene status=pending."""
        resp = await client.post(
            "/api/v1/packages/",
            json=PACKAGE_DATA,
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == "pending"
