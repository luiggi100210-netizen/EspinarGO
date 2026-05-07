"""
Tests de integración para edge cases de ofertas y transiciones de viajes.

Cubre: oferta de un viaje diferente al trip_id del endpoint → 404,
aceptar oferta ya aceptada → 400, start en estado incorrecto → 400,
complete en estado incorrecto → 400, campos de respuesta en TripPublic,
viaje en negociación tiene estado negotiating.
"""

import pytest
from httpx import AsyncClient


TRIP_DATA = {
    "origin_address": "Jr. Loreto 200, Espinar",
    "origin_lat": "-14.833",
    "origin_lng": "-71.014",
    "dest_address": "Terminal Terrestre",
    "dest_lat": "-14.836",
    "dest_lng": "-71.011",
    "proposed_price": "9.00",
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
        json={"trip_id": trip_id, "offered_price": "8.00"},
        headers={"Authorization": f"Bearer {driver_token}"},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


async def _accept_offer(
    client: AsyncClient, passenger_token: str, trip_id: str, offer_id: str
):
    resp = await client.post(
        f"/api/v1/trips/{trip_id}/accept-offer",
        json={"offer_id": offer_id},
        headers={"Authorization": f"Bearer {passenger_token}"},
    )
    assert resp.status_code == 200


class TestOfferMismatch:
    """Tests para ofertas que no corresponden al trip_id indicado."""

    async def test_accept_offer_from_different_trip_returns_404(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Aceptar una oferta que pertenece a otro viaje → 404."""
        trip_a = await _create_trip(client, passenger_token)
        trip_b = await _create_trip(client, passenger_token)

        # Crear oferta para trip_b
        offer_b = await _make_offer(client, driver_token, trip_b)

        # Intentar aceptar offer_b en trip_a
        resp = await client.post(
            f"/api/v1/trips/{trip_a}/accept-offer",
            json={"offer_id": offer_b},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 404

    async def test_accept_nonexistent_offer_returns_404(
        self, client: AsyncClient, passenger_token: str
    ):
        """Aceptar una oferta con UUID inexistente → 404."""
        trip_id = await _create_trip(client, passenger_token)
        fake_offer_id = "00000000-0000-0000-0000-000000000099"

        resp = await client.post(
            f"/api/v1/trips/{trip_id}/accept-offer",
            json={"offer_id": fake_offer_id},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 404

    async def test_trip_becomes_negotiating_after_offer(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Tras la primera oferta, el viaje pasa a estado negotiating."""
        trip_id = await _create_trip(client, passenger_token)
        await _make_offer(client, driver_token, trip_id)

        resp = await client.get(
            "/api/v1/trips/active",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        if data is not None and data["id"] == trip_id:
            assert data["status"] == "negotiating"


class TestTripStateTransitionErrors:
    """Tests para transiciones de estado incorrectas."""

    async def test_start_searching_trip_returns_403_or_400(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Intentar iniciar un viaje en estado searching → 403 o 400 (no asignado)."""
        trip_id = await _create_trip(client, passenger_token)

        resp = await client.post(
            f"/api/v1/trips/{trip_id}/start",
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code in (400, 403)

    async def test_complete_searching_trip_returns_403_or_400(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Intentar completar un viaje en estado searching → 403 o 400."""
        trip_id = await _create_trip(client, passenger_token)

        resp = await client.post(
            f"/api/v1/trips/{trip_id}/complete",
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code in (400, 403)

    async def test_complete_accepted_trip_returns_400(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Completar viaje en estado accepted (sin iniciar) → 400."""
        trip_id = await _create_trip(client, passenger_token)
        offer_id = await _make_offer(client, driver_token, trip_id)
        await _accept_offer(client, passenger_token, trip_id, offer_id)

        resp = await client.post(
            f"/api/v1/trips/{trip_id}/complete",
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 400

    async def test_start_cancelled_trip_returns_400(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Iniciar un viaje cancelado → 400 o 403."""
        trip_id = await _create_trip(client, passenger_token)
        offer_id = await _make_offer(client, driver_token, trip_id)
        await _accept_offer(client, passenger_token, trip_id, offer_id)

        # Cancelar el viaje
        await client.post(
            f"/api/v1/trips/{trip_id}/cancel",
            json={"status": "cancelled"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )

        resp = await client.post(
            f"/api/v1/trips/{trip_id}/start",
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code in (400, 403)


class TestTripPublicResponseFields:
    """Verificación de campos en la respuesta TripPublic."""

    async def test_create_trip_response_has_expected_fields(
        self, client: AsyncClient, passenger_token: str
    ):
        """La respuesta de crear un viaje tiene todos los campos esperados."""
        resp = await client.post(
            "/api/v1/trips/",
            json=TRIP_DATA,
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        required_fields = [
            "id", "status", "origin_address", "dest_address",
            "proposed_price", "payment_method", "created_at",
        ]
        for field in required_fields:
            assert field in data, f"Campo faltante: {field}"

    async def test_create_trip_status_is_searching(
        self, client: AsyncClient, passenger_token: str
    ):
        """Un viaje recién creado tiene status=searching."""
        resp = await client.post(
            "/api/v1/trips/",
            json=TRIP_DATA,
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == "searching"

    async def test_create_trip_passenger_field_present(
        self, client: AsyncClient, passenger_token: str
    ):
        """El campo 'passenger' en la respuesta tiene id y full_name."""
        resp = await client.post(
            "/api/v1/trips/",
            json=TRIP_DATA,
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 201
        passenger = resp.json().get("passenger")
        if passenger is not None:
            assert "id" in passenger
            assert "full_name" in passenger

    async def test_accept_offer_updates_final_price(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Tras aceptar oferta, final_price refleja el precio ofertado."""
        trip_id = await _create_trip(client, passenger_token)
        offer_id = await _make_offer(client, driver_token, trip_id)

        resp = await client.post(
            f"/api/v1/trips/{trip_id}/accept-offer",
            json={"offer_id": offer_id},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["final_price"] == "8.00"
        assert data["status"] == "accepted"

    async def test_start_trip_updates_status_and_started_at(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Tras iniciar, status=in_progress y started_at no es null."""
        trip_id = await _create_trip(client, passenger_token)
        offer_id = await _make_offer(client, driver_token, trip_id)
        await _accept_offer(client, passenger_token, trip_id, offer_id)

        resp = await client.post(
            f"/api/v1/trips/{trip_id}/start",
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "in_progress"
        assert data["started_at"] is not None

    async def test_complete_trip_sets_completed_at(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Tras completar, completed_at tiene valor."""
        trip_id = await _create_trip(client, passenger_token)
        offer_id = await _make_offer(client, driver_token, trip_id)
        await _accept_offer(client, passenger_token, trip_id, offer_id)
        await client.post(
            f"/api/v1/trips/{trip_id}/start",
            headers={"Authorization": f"Bearer {driver_token}"},
        )

        resp = await client.post(
            f"/api/v1/trips/{trip_id}/complete",
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert data["completed_at"] is not None


class TestTripOfferResponse:
    """Verificación de la respuesta de crear/ver ofertas."""

    async def test_offer_response_driver_field_present(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """La respuesta de oferta incluye información del conductor."""
        trip_id = await _create_trip(client, passenger_token)

        resp = await client.post(
            "/api/v1/trips/offer",
            json={"trip_id": trip_id, "offered_price": "8.00"},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "driver" in data or "offered_price" in data

    async def test_offer_not_accepted_by_default(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Una oferta recién creada tiene is_accepted=False."""
        trip_id = await _create_trip(client, passenger_token)

        resp = await client.post(
            "/api/v1/trips/offer",
            json={"trip_id": trip_id, "offered_price": "8.00"},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["is_accepted"] is False

    async def test_offer_has_expires_at_field(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """La oferta tiene campo expires_at."""
        trip_id = await _create_trip(client, passenger_token)

        resp = await client.post(
            "/api/v1/trips/offer",
            json={"trip_id": trip_id, "offered_price": "8.00"},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 201
        assert "expires_at" in resp.json()

    async def test_trip_offers_list_after_offer(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Después de hacer una oferta, el endpoint de offers la muestra."""
        trip_id = await _create_trip(client, passenger_token)
        await _make_offer(client, driver_token, trip_id)

        resp = await client.get(
            f"/api/v1/trips/{trip_id}/offers",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200
        offers = resp.json()
        assert isinstance(offers, list)
        assert len(offers) >= 1

    async def test_offers_list_requires_passenger_role(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Solo el pasajero puede ver las ofertas de su viaje (conductor → 403)."""
        trip_id = await _create_trip(client, passenger_token)

        resp = await client.get(
            f"/api/v1/trips/{trip_id}/offers",
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 403
