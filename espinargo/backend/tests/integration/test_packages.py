"""
Tests de integración para el flujo completo de encomiendas.
"""

import pytest
from httpx import AsyncClient


PACKAGE_DATA = {
    "recipient_name": "María López",
    "recipient_phone": "+51987654321",
    "delivery_address": "Jr. Junín 123, Espinar",
    "size": "small",
    "description": "Ropa y documentos",
    "is_fragile": False,
    "payment_method": "cash",
}


class TestPackageFlow:

    async def test_create_package(self, client: AsyncClient, passenger_token: str):
        resp = await client.post(
            "/api/v1/packages/",
            json=PACKAGE_DATA,
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "pending"
        assert data["tracking_code"].startswith("ESP-")
        assert data["recipient_name"] == "María López"

    async def test_track_package_by_code(self, client: AsyncClient, passenger_token: str):
        create_resp = await client.post(
            "/api/v1/packages/",
            json=PACKAGE_DATA,
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        tracking_code = create_resp.json()["tracking_code"]

        resp = await client.get(f"/api/v1/packages/track/{tracking_code}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["package"]["tracking_code"] == tracking_code
        assert len(data["tracking_history"]) >= 1

    async def test_track_invalid_code(self, client: AsyncClient):
        resp = await client.get("/api/v1/packages/track/INVALID-CODE")
        assert resp.status_code == 404

    async def test_get_my_packages(self, client: AsyncClient, passenger_token: str):
        await client.post(
            "/api/v1/packages/",
            json=PACKAGE_DATA,
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        resp = await client.get(
            "/api/v1/packages/my",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["meta"]["total"] >= 1

    async def test_driver_assigns_package(self, client: AsyncClient, passenger_token: str, driver_token: str):
        create_resp = await client.post(
            "/api/v1/packages/",
            json=PACKAGE_DATA,
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        package_id = create_resp.json()["id"]

        resp = await client.post(
            f"/api/v1/packages/{package_id}/assign",
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "assigned"

    async def test_cannot_assign_twice(self, client: AsyncClient, passenger_token: str, driver_token: str):
        create_resp = await client.post(
            "/api/v1/packages/",
            json=PACKAGE_DATA,
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        package_id = create_resp.json()["id"]

        await client.post(
            f"/api/v1/packages/{package_id}/assign",
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        resp = await client.post(
            f"/api/v1/packages/{package_id}/assign",
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 400

    async def test_full_package_lifecycle(self, client: AsyncClient, passenger_token: str, driver_token: str):
        create_resp = await client.post(
            "/api/v1/packages/",
            json=PACKAGE_DATA,
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        package_id = create_resp.json()["id"]

        await client.post(
            f"/api/v1/packages/{package_id}/assign",
            headers={"Authorization": f"Bearer {driver_token}"},
        )

        pickup_resp = await client.post(
            f"/api/v1/packages/{package_id}/update-status",
            json={"status": "picked_up"},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert pickup_resp.status_code == 200
        assert pickup_resp.json()["status"] == "picked_up"

        transit_resp = await client.post(
            f"/api/v1/packages/{package_id}/update-status",
            json={"status": "in_transit"},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert transit_resp.status_code == 200

        delivered_resp = await client.post(
            f"/api/v1/packages/{package_id}/update-status",
            json={"status": "delivered"},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert delivered_resp.status_code == 200
        assert delivered_resp.json()["status"] == "delivered"

        tracking_resp = await client.get(
            f"/api/v1/packages/track/{create_resp.json()['tracking_code']}"
        )
        assert len(tracking_resp.json()["tracking_history"]) == 5

    async def test_invalid_status_transition(self, client: AsyncClient, passenger_token: str, driver_token: str):
        create_resp = await client.post(
            "/api/v1/packages/",
            json=PACKAGE_DATA,
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        package_id = create_resp.json()["id"]

        await client.post(
            f"/api/v1/packages/{package_id}/assign",
            headers={"Authorization": f"Bearer {driver_token}"},
        )

        resp = await client.post(
            f"/api/v1/packages/{package_id}/update-status",
            json={"status": "delivered"},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 400
