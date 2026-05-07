"""
Tests de integración extendidos para viajes.

Cubre: lista de ofertas, cancelaciones de borde, historial de conductor.
"""

import pytest
from httpx import AsyncClient


TRIP_DATA = {
    "origin_address": "Plaza de Armas, Espinar",
    "origin_lat": "-14.832",
    "origin_lng": "-71.013",
    "dest_address": "Mercado Central, Espinar",
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


async def _make_offer(client: AsyncClient, driver_token: str, trip_id: str, price: str = "7.50") -> str:
    resp = await client.post(
        "/api/v1/trips/offer",
        json={"trip_id": trip_id, "offered_price": price},
        headers={"Authorization": f"Bearer {driver_token}"},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


async def _accept_offer(client: AsyncClient, passenger_token: str, trip_id: str, offer_id: str):
    resp = await client.post(
        f"/api/v1/trips/{trip_id}/accept-offer",
        json={"offer_id": offer_id},
        headers={"Authorization": f"Bearer {passenger_token}"},
    )
    assert resp.status_code == 200


class TestTripOffers:
    """Tests para el endpoint GET /{trip_id}/offers."""

    async def test_passenger_sees_pending_offers(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Pasajero puede ver las ofertas activas de su viaje."""
        trip_id = await _create_trip(client, passenger_token)
        await _make_offer(client, driver_token, trip_id)

        resp = await client.get(
            f"/api/v1/trips/{trip_id}/offers",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200
        offers = resp.json()
        assert len(offers) >= 1
        assert offers[0]["offered_price"] == "7.50"

    async def test_driver_cannot_see_trip_offers(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Conductor no puede ver las ofertas de un viaje ajeno (solo pasajero)."""
        trip_id = await _create_trip(client, passenger_token)

        resp = await client.get(
            f"/api/v1/trips/{trip_id}/offers",
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        # Solo el pasajero dueño puede ver las ofertas
        assert resp.status_code in (403, 401)

    async def test_nonexistent_trip_offers_404(
        self, client: AsyncClient, passenger_token: str
    ):
        """Trip inexistente → 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.get(
            f"/api/v1/trips/{fake_id}/offers",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 404

    async def test_unauthenticated_cannot_see_offers(
        self, client: AsyncClient, passenger_token: str
    ):
        """Sin token → 401."""
        trip_id = await _create_trip(client, passenger_token)
        resp = await client.get(f"/api/v1/trips/{trip_id}/offers")
        assert resp.status_code == 401


class TestTripCancellation:
    """Tests de casos borde en cancelación de viajes."""

    async def test_cannot_cancel_completed_trip(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """No se puede cancelar un viaje ya completado."""
        trip_id = await _create_trip(client, passenger_token)
        offer_id = await _make_offer(client, driver_token, trip_id)
        await _accept_offer(client, passenger_token, trip_id, offer_id)
        await client.post(
            f"/api/v1/trips/{trip_id}/start",
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        await client.post(
            f"/api/v1/trips/{trip_id}/complete",
            headers={"Authorization": f"Bearer {driver_token}"},
        )

        resp = await client.post(
            f"/api/v1/trips/{trip_id}/cancel",
            json={"status": "cancelled"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 400

    async def test_cannot_complete_non_in_progress_trip(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """No se puede completar un viaje que no está en curso."""
        trip_id = await _create_trip(client, passenger_token)
        offer_id = await _make_offer(client, driver_token, trip_id)
        await _accept_offer(client, passenger_token, trip_id, offer_id)
        # Estado: accepted, no in_progress todavía

        resp = await client.post(
            f"/api/v1/trips/{trip_id}/complete",
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 400

    async def test_driver_cancels_accepted_trip(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """El conductor puede cancelar un viaje aceptado."""
        trip_id = await _create_trip(client, passenger_token)
        offer_id = await _make_offer(client, driver_token, trip_id)
        await _accept_offer(client, passenger_token, trip_id, offer_id)

        resp = await client.post(
            f"/api/v1/trips/{trip_id}/cancel",
            json={"status": "cancelled"},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"

    async def test_third_party_cannot_cancel_trip(
        self, client: AsyncClient, passenger_token: str, admin_token: str
    ):
        """Un usuario ajeno al viaje no puede cancelarlo."""
        trip_id = await _create_trip(client, passenger_token)

        resp = await client.post(
            f"/api/v1/trips/{trip_id}/cancel",
            json={"status": "cancelled"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 403

    async def test_cancel_nonexistent_trip(
        self, client: AsyncClient, passenger_token: str
    ):
        """Trip inexistente → 404."""
        fake_id = "00000000-0000-0000-0000-000000000001"
        resp = await client.post(
            f"/api/v1/trips/{fake_id}/cancel",
            json={"status": "cancelled"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 404


class TestDriverHistory:
    """Tests para historial de viajes desde el rol conductor."""

    async def test_driver_sees_completed_trips(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """El conductor puede ver sus viajes completados en el historial."""
        # Completar un viaje
        trip_id = await _create_trip(client, passenger_token)
        offer_id = await _make_offer(client, driver_token, trip_id)
        await _accept_offer(client, passenger_token, trip_id, offer_id)
        await client.post(f"/api/v1/trips/{trip_id}/start", headers={"Authorization": f"Bearer {driver_token}"})
        await client.post(f"/api/v1/trips/{trip_id}/complete", headers={"Authorization": f"Bearer {driver_token}"})

        resp = await client.get(
            "/api/v1/trips/history",
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["meta"]["total"] >= 1

    async def test_history_pagination(
        self, client: AsyncClient, passenger_token: str
    ):
        """Paginación del historial funciona correctamente."""
        resp = await client.get(
            "/api/v1/trips/history?page=1&per_page=5",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200
        meta = resp.json()["meta"]
        assert meta["page"] == 1
        assert meta["per_page"] == 5

    async def test_history_unauthenticated(self, client: AsyncClient):
        """Sin token → 401."""
        resp = await client.get("/api/v1/trips/history")
        assert resp.status_code == 401


class TestCreateTripValidation:
    """Validaciones al crear viajes."""

    async def test_missing_required_fields(self, client: AsyncClient, passenger_token: str):
        """Campos obligatorios faltantes → 422."""
        resp = await client.post(
            "/api/v1/trips/",
            json={"origin_address": "Solo origen"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 422

    async def test_unauthenticated_cannot_create_trip(self, client: AsyncClient):
        resp = await client.post("/api/v1/trips/", json=TRIP_DATA)
        assert resp.status_code == 401
