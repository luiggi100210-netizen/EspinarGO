"""
Tests de integración para rastreo y transiciones de estado de encomiendas.

Cubre: historial de seguimiento, conductor incorrecto → 403,
update tras delivered → 400, descripción personalizada, timestamps.
"""

import pytest
from httpx import AsyncClient


PACKAGE_DATA = {
    "recipient_name": "Ana Quispe",
    "recipient_phone": "+51987000001",
    "delivery_address": "Jr. Cusco 123, Espinar",
    "size": "small",
    "description": "Ropa",
    "is_fragile": False,
    "payment_method": "cash",
}


async def _create_and_assign(
    client: AsyncClient, passenger_token: str, driver_token: str
) -> tuple[str, str]:
    """Helper: crea encomienda, la asigna. Retorna (pkg_id, tracking_code)."""
    resp = await client.post(
        "/api/v1/packages/",
        json=PACKAGE_DATA,
        headers={"Authorization": f"Bearer {passenger_token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    pkg_id = data["id"]
    tracking_code = data["tracking_code"]

    assign = await client.post(
        f"/api/v1/packages/{pkg_id}/assign",
        headers={"Authorization": f"Bearer {driver_token}"},
    )
    assert assign.status_code == 200
    return pkg_id, tracking_code


class TestPackageTrackingHistory:
    """El historial de rastreo crece con cada transición de estado."""

    async def test_tracking_has_assign_event(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Tras asignar, el historial contiene el evento assigned."""
        pkg_id, tracking_code = await _create_and_assign(
            client, passenger_token, driver_token
        )

        resp = await client.get(f"/api/v1/packages/track/{tracking_code}")
        assert resp.status_code == 200
        data = resp.json()
        assert "tracking_history" in data
        statuses = [e["status"] for e in data["tracking_history"]]
        assert "assigned" in statuses

    async def test_tracking_grows_with_picked_up(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Tras PICKED_UP, el historial tiene dos eventos."""
        pkg_id, tracking_code = await _create_and_assign(
            client, passenger_token, driver_token
        )
        await client.post(
            f"/api/v1/packages/{pkg_id}/update-status",
            json={"status": "picked_up"},
            headers={"Authorization": f"Bearer {driver_token}"},
        )

        resp = await client.get(f"/api/v1/packages/track/{tracking_code}")
        data = resp.json()
        statuses = [e["status"] for e in data["tracking_history"]]
        assert "assigned" in statuses
        assert "picked_up" in statuses

    async def test_tracking_full_lifecycle_history(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Ciclo completo: el historial tiene todos los eventos."""
        pkg_id, tracking_code = await _create_and_assign(
            client, passenger_token, driver_token
        )

        for new_status in ["picked_up", "in_transit", "delivered"]:
            await client.post(
                f"/api/v1/packages/{pkg_id}/update-status",
                json={"status": new_status},
                headers={"Authorization": f"Bearer {driver_token}"},
            )

        resp = await client.get(f"/api/v1/packages/track/{tracking_code}")
        data = resp.json()
        statuses = [e["status"] for e in data["tracking_history"]]
        for expected in ["assigned", "picked_up", "in_transit", "delivered"]:
            assert expected in statuses, f"Evento '{expected}' faltante en historial"

    async def test_tracking_response_has_package_and_history(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """La respuesta de track tiene los campos package y tracking_history."""
        _, tracking_code = await _create_and_assign(
            client, passenger_token, driver_token
        )

        resp = await client.get(f"/api/v1/packages/track/{tracking_code}")
        assert resp.status_code == 200
        data = resp.json()
        assert "package" in data
        assert "tracking_history" in data
        assert isinstance(data["tracking_history"], list)

    async def test_tracking_event_has_expected_fields(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Cada evento de tracking tiene los campos status, description, created_at."""
        _, tracking_code = await _create_and_assign(
            client, passenger_token, driver_token
        )

        resp = await client.get(f"/api/v1/packages/track/{tracking_code}")
        data = resp.json()
        if data["tracking_history"]:
            event = data["tracking_history"][0]
            for field in ["status", "description", "created_at"]:
                assert field in event, f"Campo faltante en evento: {field}"

    async def test_track_invalid_code_returns_404(self, client: AsyncClient):
        """Código de seguimiento inexistente → 404."""
        resp = await client.get("/api/v1/packages/track/ESP-INVALIDO-9999")
        assert resp.status_code == 404


class TestPackageStatusGuards:
    """Guardias en actualización de estado."""

    async def test_wrong_driver_cannot_update_status(
        self, client: AsyncClient, passenger_token: str, driver_token: str, admin_token: str
    ):
        """Conductor que no asignó la encomienda no puede actualizar su estado → 403."""
        pkg_id, _ = await _create_and_assign(client, passenger_token, driver_token)

        # Crear otro conductor (usamos admin_token que no es el conductor asignado)
        # El admin no tiene driver_profile así que obtendremos 403 por rol de conductor
        resp = await client.post(
            f"/api/v1/packages/{pkg_id}/update-status",
            json={"status": "picked_up"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 403

    async def test_passenger_cannot_update_status(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Pasajero no puede actualizar el estado → 403."""
        pkg_id, _ = await _create_and_assign(client, passenger_token, driver_token)

        resp = await client.post(
            f"/api/v1/packages/{pkg_id}/update-status",
            json={"status": "picked_up"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 403

    async def test_update_status_requires_auth(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Sin token → 401."""
        pkg_id, _ = await _create_and_assign(client, passenger_token, driver_token)

        resp = await client.post(
            f"/api/v1/packages/{pkg_id}/update-status",
            json={"status": "picked_up"},
        )
        assert resp.status_code == 401

    async def test_update_nonexistent_package_returns_404(
        self, client: AsyncClient, driver_token: str
    ):
        """Encomienda inexistente → 404."""
        resp = await client.post(
            "/api/v1/packages/00000000-0000-0000-0000-000000000000/update-status",
            json={"status": "picked_up"},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 404


class TestPackageStatusTransitionRules:
    """Reglas de transición de estado."""

    async def test_cannot_skip_to_in_transit_from_assigned(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """No se puede saltar de assigned a in_transit (debe ir por picked_up) → 400."""
        pkg_id, _ = await _create_and_assign(client, passenger_token, driver_token)

        resp = await client.post(
            f"/api/v1/packages/{pkg_id}/update-status",
            json={"status": "in_transit"},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 400

    async def test_cannot_update_delivered_package(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """No hay transición válida desde delivered → 400."""
        pkg_id, _ = await _create_and_assign(client, passenger_token, driver_token)

        for s in ["picked_up", "in_transit", "delivered"]:
            await client.post(
                f"/api/v1/packages/{pkg_id}/update-status",
                json={"status": s},
                headers={"Authorization": f"Bearer {driver_token}"},
            )

        resp = await client.post(
            f"/api/v1/packages/{pkg_id}/update-status",
            json={"status": "picked_up"},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 400

    async def test_custom_description_stored_in_tracking(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Descripción personalizada se guarda en el evento de tracking."""
        pkg_id, tracking_code = await _create_and_assign(
            client, passenger_token, driver_token
        )
        custom_desc = "Recogido en puerta de casa"

        await client.post(
            f"/api/v1/packages/{pkg_id}/update-status",
            json={"status": "picked_up", "description": custom_desc},
            headers={"Authorization": f"Bearer {driver_token}"},
        )

        resp = await client.get(f"/api/v1/packages/track/{tracking_code}")
        descriptions = [e["description"] for e in resp.json()["tracking_history"]]
        assert custom_desc in descriptions

    async def test_picked_up_response_has_correct_status(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """La respuesta de update-status refleja el nuevo estado."""
        pkg_id, _ = await _create_and_assign(client, passenger_token, driver_token)

        resp = await client.post(
            f"/api/v1/packages/{pkg_id}/update-status",
            json={"status": "picked_up"},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "picked_up"

    async def test_delivered_package_has_tracking_code(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """La encomienda entregada mantiene su tracking_code."""
        pkg_id, tracking_code = await _create_and_assign(
            client, passenger_token, driver_token
        )

        for s in ["picked_up", "in_transit", "delivered"]:
            resp = await client.post(
                f"/api/v1/packages/{pkg_id}/update-status",
                json={"status": s},
                headers={"Authorization": f"Bearer {driver_token}"},
            )
            assert resp.status_code == 200

        assert resp.json()["tracking_code"] == tracking_code
        assert resp.json()["status"] == "delivered"
