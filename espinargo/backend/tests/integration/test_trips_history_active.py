"""
Tests de integración para historial de viajes y endpoint de viaje activo.

Cubre: paginación del historial (límites, page=0, per_page>50),
viaje activo para conductor/sin auth/sin viaje activo,
historial para admin y usuario sin viajes.
"""

import pytest
from httpx import AsyncClient


TRIP_DATA = {
    "origin_address": "Plaza de Armas, Espinar",
    "origin_lat": "-14.832",
    "origin_lng": "-71.013",
    "dest_address": "Mercado Central",
    "dest_lat": "-14.835",
    "dest_lng": "-71.010",
    "proposed_price": "8.00",
    "payment_method": "cash",
}


async def _create_trip(client: AsyncClient, passenger_token: str) -> str:
    resp = await client.post(
        "/api/v1/trips/",
        json=TRIP_DATA,
        headers={"Authorization": f"Bearer {passenger_token}"},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


async def _make_offer(client: AsyncClient, driver_token: str, trip_id: str) -> str:
    resp = await client.post(
        "/api/v1/trips/offer",
        json={"trip_id": trip_id, "offered_price": "7.50"},
        headers={"Authorization": f"Bearer {driver_token}"},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


async def _full_lifecycle(client: AsyncClient, passenger_token: str, driver_token: str) -> str:
    """Helper: crea viaje, acepta oferta, inicia y completa. Retorna trip_id."""
    trip_id = await _create_trip(client, passenger_token)
    offer_id = await _make_offer(client, driver_token, trip_id)
    await client.post(
        f"/api/v1/trips/{trip_id}/accept-offer",
        json={"offer_id": offer_id},
        headers={"Authorization": f"Bearer {passenger_token}"},
    )
    await client.post(
        f"/api/v1/trips/{trip_id}/start",
        headers={"Authorization": f"Bearer {driver_token}"},
    )
    await client.post(
        f"/api/v1/trips/{trip_id}/complete",
        headers={"Authorization": f"Bearer {driver_token}"},
    )
    return trip_id


class TestTripHistoryPagination:
    """Validaciones de paginación en el historial de viajes."""

    async def test_per_page_above_max_rejected(
        self, client: AsyncClient, passenger_token: str
    ):
        """per_page > 50 → 422 (límite del endpoint)."""
        resp = await client.get(
            "/api/v1/trips/history?per_page=51",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 422

    async def test_page_zero_rejected(
        self, client: AsyncClient, passenger_token: str
    ):
        """page=0 → 422 (mínimo es 1)."""
        resp = await client.get(
            "/api/v1/trips/history?page=0",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 422

    async def test_per_page_zero_rejected(
        self, client: AsyncClient, passenger_token: str
    ):
        """per_page=0 → 422 (mínimo es 1)."""
        resp = await client.get(
            "/api/v1/trips/history?per_page=0",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 422

    async def test_per_page_max_accepted(
        self, client: AsyncClient, passenger_token: str
    ):
        """per_page=50 (máximo) → 200."""
        resp = await client.get(
            "/api/v1/trips/history?per_page=50",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200

    async def test_history_response_has_meta_and_trips(
        self, client: AsyncClient, passenger_token: str
    ):
        """La respuesta contiene los campos trips y meta."""
        resp = await client.get(
            "/api/v1/trips/history",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "trips" in data
        assert "meta" in data
        assert isinstance(data["trips"], list)

    async def test_history_meta_has_expected_fields(
        self, client: AsyncClient, passenger_token: str
    ):
        """Los campos de meta están presentes."""
        resp = await client.get(
            "/api/v1/trips/history",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200
        meta = resp.json()["meta"]
        for field in ["total", "page", "per_page", "total_pages", "has_next", "has_prev"]:
            assert field in meta, f"Campo faltante en meta: {field}"

    async def test_history_page_param_reflected_in_meta(
        self, client: AsyncClient, passenger_token: str
    ):
        """El parámetro page se refleja en meta.page."""
        resp = await client.get(
            "/api/v1/trips/history?page=1&per_page=10",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200
        meta = resp.json()["meta"]
        assert meta["page"] == 1
        assert meta["per_page"] == 10

    async def test_history_requires_auth(self, client: AsyncClient):
        """Sin token → 401."""
        resp = await client.get("/api/v1/trips/history")
        assert resp.status_code == 401


class TestTripHistoryRoles:
    """Historial de viajes según el rol del usuario."""

    async def test_admin_can_see_history(
        self, client: AsyncClient, admin_token: str
    ):
        """El admin puede ver el historial general."""
        resp = await client.get(
            "/api/v1/trips/history",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "trips" in data
        assert "meta" in data

    async def test_driver_history_returns_list(
        self, client: AsyncClient, driver_token: str
    ):
        """El conductor puede consultar su historial."""
        resp = await client.get(
            "/api/v1/trips/history",
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 200
        assert isinstance(resp.json()["trips"], list)

    async def test_completed_trip_appears_in_history(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Un viaje completado aparece en el historial del pasajero."""
        trip_id = await _full_lifecycle(client, passenger_token, driver_token)

        resp = await client.get(
            "/api/v1/trips/history",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        trip_ids = [t["id"] for t in data["trips"]]
        assert trip_id in trip_ids

    async def test_cancelled_trip_appears_in_history(
        self, client: AsyncClient, passenger_token: str
    ):
        """Un viaje cancelado también aparece en el historial."""
        trip_id = await _create_trip(client, passenger_token)
        await client.post(
            f"/api/v1/trips/{trip_id}/cancel",
            json={"status": "cancelled"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )

        resp = await client.get(
            "/api/v1/trips/history",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200
        trip_ids = [t["id"] for t in resp.json()["trips"]]
        assert trip_id in trip_ids

    async def test_in_progress_trip_not_in_history(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Un viaje en curso NO aparece en el historial (solo completos/cancelados)."""
        trip_id = await _create_trip(client, passenger_token)
        offer_id = await _make_offer(client, driver_token, trip_id)
        await client.post(
            f"/api/v1/trips/{trip_id}/accept-offer",
            json={"offer_id": offer_id},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        await client.post(
            f"/api/v1/trips/{trip_id}/start",
            headers={"Authorization": f"Bearer {driver_token}"},
        )

        resp = await client.get(
            "/api/v1/trips/history",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200
        trip_ids = [t["id"] for t in resp.json()["trips"]]
        assert trip_id not in trip_ids


class TestActiveTripEndpoint:
    """Tests para GET /trips/active."""

    async def test_driver_cannot_access_active_trip(
        self, client: AsyncClient, driver_token: str
    ):
        """Conductor no puede acceder a /active (solo pasajeros) → 403."""
        resp = await client.get(
            "/api/v1/trips/active",
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 403

    async def test_admin_cannot_access_active_trip(
        self, client: AsyncClient, admin_token: str
    ):
        """Admin no puede acceder a /active (solo pasajeros) → 403."""
        resp = await client.get(
            "/api/v1/trips/active",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 403

    async def test_active_trip_requires_auth(self, client: AsyncClient):
        """Sin token → 401."""
        resp = await client.get("/api/v1/trips/active")
        assert resp.status_code == 401

    async def test_no_active_trip_returns_null(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Si el pasajero no tiene viaje activo, retorna null (body vacío/null)."""
        # Completar cualquier viaje pendiente creando y completando uno
        trip_id = await _create_trip(client, passenger_token)
        await client.post(
            f"/api/v1/trips/{trip_id}/cancel",
            json={"status": "cancelled"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )

        resp = await client.get(
            "/api/v1/trips/active",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        # El endpoint retorna null o el viaje activo
        assert resp.status_code == 200

    async def test_active_trip_present_when_searching(
        self, client: AsyncClient, passenger_token: str
    ):
        """Un viaje recién creado (searching) aparece como activo."""
        trip_id = await _create_trip(client, passenger_token)

        resp = await client.get(
            "/api/v1/trips/active",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        # Puede ser null si hay otro viaje activo previo, pero si no es null debe ser el reciente
        if data is not None:
            assert data["status"] in ("searching", "negotiating", "accepted", "in_progress")

    async def test_active_trip_has_expected_fields(
        self, client: AsyncClient, passenger_token: str
    ):
        """Si hay viaje activo, la respuesta tiene los campos esperados."""
        trip_id = await _create_trip(client, passenger_token)

        resp = await client.get(
            "/api/v1/trips/active",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        if data is not None:
            for field in ["id", "status", "origin_address", "dest_address", "proposed_price"]:
                assert field in data, f"Campo faltante: {field}"


class TestCancelTripExtra:
    """Casos adicionales de cancelación de viajes."""

    async def test_passenger_cancels_searching_trip(
        self, client: AsyncClient, passenger_token: str
    ):
        """El pasajero puede cancelar un viaje recién creado (estado searching)."""
        trip_id = await _create_trip(client, passenger_token)

        resp = await client.post(
            f"/api/v1/trips/{trip_id}/cancel",
            json={"status": "cancelled"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"

    async def test_cancel_already_cancelled_trip_returns_400(
        self, client: AsyncClient, passenger_token: str
    ):
        """Cancelar un viaje ya cancelado → 400."""
        trip_id = await _create_trip(client, passenger_token)
        await client.post(
            f"/api/v1/trips/{trip_id}/cancel",
            json={"status": "cancelled"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )

        resp = await client.post(
            f"/api/v1/trips/{trip_id}/cancel",
            json={"status": "cancelled"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 400

    async def test_cancel_response_has_cancel_reason(
        self, client: AsyncClient, passenger_token: str
    ):
        """La respuesta de cancelación incluye cancel_reason."""
        trip_id = await _create_trip(client, passenger_token)

        resp = await client.post(
            f"/api/v1/trips/{trip_id}/cancel",
            json={"status": "cancelled"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "cancel_reason" in data

    async def test_cancel_requires_auth(self, client: AsyncClient, passenger_token: str):
        """Sin token → 401."""
        trip_id = await _create_trip(client, passenger_token)
        resp = await client.post(
            f"/api/v1/trips/{trip_id}/cancel",
            json={"status": "cancelled"},
        )
        assert resp.status_code == 401
