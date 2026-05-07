"""
Tests de integración para la máquina de estados de viajes.

Cubre: guardias de rol en start/complete, conductor incorrecto,
oferta sobre viaje ya aceptado, nonexistentes.
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


async def _accept_offer(
    client: AsyncClient, passenger_token: str, trip_id: str, offer_id: str
):
    resp = await client.post(
        f"/api/v1/trips/{trip_id}/accept-offer",
        json={"offer_id": offer_id},
        headers={"Authorization": f"Bearer {passenger_token}"},
    )
    assert resp.status_code == 200


async def _full_accept(
    client: AsyncClient, passenger_token: str, driver_token: str
) -> str:
    """Helper: crea viaje, hace oferta y la acepta. Retorna trip_id."""
    trip_id = await _create_trip(client, passenger_token)
    offer_id = await _make_offer(client, driver_token, trip_id)
    await _accept_offer(client, passenger_token, trip_id, offer_id)
    return trip_id


class TestStartTripGuards:
    """Guardias de acceso en el endpoint /start."""

    async def test_passenger_cannot_start_trip(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Pasajero intenta iniciar su propio viaje → 403 (solo conductor)."""
        trip_id = await _full_accept(client, passenger_token, driver_token)

        resp = await client.post(
            f"/api/v1/trips/{trip_id}/start",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 403

    async def test_admin_cannot_start_trip(
        self, client: AsyncClient, passenger_token: str, driver_token: str, admin_token: str
    ):
        """Admin no puede iniciar viaje → 403 (solo conductor asignado)."""
        trip_id = await _full_accept(client, passenger_token, driver_token)

        resp = await client.post(
            f"/api/v1/trips/{trip_id}/start",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 403

    async def test_start_nonexistent_trip_returns_404(
        self, client: AsyncClient, driver_token: str
    ):
        """Trip inexistente → 404."""
        resp = await client.post(
            "/api/v1/trips/00000000-0000-0000-0000-000000000000/start",
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 404

    async def test_start_requires_auth(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Sin token → 401."""
        trip_id = await _full_accept(client, passenger_token, driver_token)
        resp = await client.post(f"/api/v1/trips/{trip_id}/start")
        assert resp.status_code == 401

    async def test_start_trip_returns_in_progress(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """El conductor asignado puede iniciar el viaje correctamente."""
        trip_id = await _full_accept(client, passenger_token, driver_token)

        resp = await client.post(
            f"/api/v1/trips/{trip_id}/start",
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "in_progress"


class TestCompleteTripGuards:
    """Guardias de acceso en el endpoint /complete."""

    async def test_passenger_cannot_complete_trip(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Pasajero no puede completar el viaje → 403."""
        trip_id = await _full_accept(client, passenger_token, driver_token)
        await client.post(
            f"/api/v1/trips/{trip_id}/start",
            headers={"Authorization": f"Bearer {driver_token}"},
        )

        resp = await client.post(
            f"/api/v1/trips/{trip_id}/complete",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 403

    async def test_admin_cannot_complete_trip(
        self, client: AsyncClient, passenger_token: str, driver_token: str, admin_token: str
    ):
        """Admin no puede completar un viaje → 403."""
        trip_id = await _full_accept(client, passenger_token, driver_token)
        await client.post(
            f"/api/v1/trips/{trip_id}/start",
            headers={"Authorization": f"Bearer {driver_token}"},
        )

        resp = await client.post(
            f"/api/v1/trips/{trip_id}/complete",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 403

    async def test_complete_nonexistent_trip_returns_404(
        self, client: AsyncClient, driver_token: str
    ):
        """Trip inexistente → 404."""
        resp = await client.post(
            "/api/v1/trips/00000000-0000-0000-0000-000000000000/complete",
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 404

    async def test_complete_requires_auth(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Sin token → 401."""
        trip_id = await _full_accept(client, passenger_token, driver_token)
        await client.post(
            f"/api/v1/trips/{trip_id}/start",
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        resp = await client.post(f"/api/v1/trips/{trip_id}/complete")
        assert resp.status_code == 401

    async def test_complete_trip_returns_completed(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """El conductor puede completar el viaje en curso."""
        trip_id = await _full_accept(client, passenger_token, driver_token)
        await client.post(
            f"/api/v1/trips/{trip_id}/start",
            headers={"Authorization": f"Bearer {driver_token}"},
        )

        resp = await client.post(
            f"/api/v1/trips/{trip_id}/complete",
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"


class TestOfferEdgeCases:
    """Casos borde al hacer ofertas."""

    async def test_offer_on_accepted_trip_returns_400(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Hacer oferta a un viaje ya aceptado → 400."""
        trip_id = await _create_trip(client, passenger_token)
        offer_id = await _make_offer(client, driver_token, trip_id)
        await _accept_offer(client, passenger_token, trip_id, offer_id)

        # Intentar otra oferta sobre el viaje ya aceptado
        resp = await client.post(
            "/api/v1/trips/offer",
            json={"trip_id": trip_id, "offered_price": "6.00"},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 400

    async def test_passenger_cannot_make_offer(
        self, client: AsyncClient, passenger_token: str
    ):
        """Pasajero no puede hacer ofertas (solo conductor) → 403."""
        trip_id = await _create_trip(client, passenger_token)

        resp = await client.post(
            "/api/v1/trips/offer",
            json={"trip_id": trip_id, "offered_price": "6.00"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 403

    async def test_accept_nonexistent_offer_returns_404(
        self, client: AsyncClient, passenger_token: str
    ):
        """Aceptar oferta inexistente → 404."""
        trip_id = await _create_trip(client, passenger_token)

        resp = await client.post(
            f"/api/v1/trips/{trip_id}/accept-offer",
            json={"offer_id": "00000000-0000-0000-0000-000000000000"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 404

    async def test_offer_missing_price_returns_422(
        self, client: AsyncClient, driver_token: str, passenger_token: str
    ):
        """Oferta sin precio → 422."""
        trip_id = await _create_trip(client, passenger_token)

        resp = await client.post(
            "/api/v1/trips/offer",
            json={"trip_id": trip_id},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 422

    async def test_offer_response_has_expected_fields(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """La respuesta de una oferta tiene los campos esperados."""
        trip_id = await _create_trip(client, passenger_token)

        resp = await client.post(
            "/api/v1/trips/offer",
            json={"trip_id": trip_id, "offered_price": "7.00"},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        for field in ["id", "offered_price", "is_accepted", "expires_at"]:
            assert field in data, f"Campo faltante: {field}"


class TestAcceptOfferGuards:
    """Guardias en aceptar oferta."""

    async def test_driver_cannot_accept_offer(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Conductor no puede aceptar ofertas de su propio trip → 403."""
        trip_id = await _create_trip(client, passenger_token)
        offer_id = await _make_offer(client, driver_token, trip_id)

        resp = await client.post(
            f"/api/v1/trips/{trip_id}/accept-offer",
            json={"offer_id": offer_id},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 403

    async def test_accept_offer_requires_auth(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Sin token → 401."""
        trip_id = await _create_trip(client, passenger_token)
        offer_id = await _make_offer(client, driver_token, trip_id)

        resp = await client.post(
            f"/api/v1/trips/{trip_id}/accept-offer",
            json={"offer_id": offer_id},
        )
        assert resp.status_code == 401

    async def test_accept_offer_returns_accepted_status(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Aceptar una oferta válida cambia el estado a accepted."""
        trip_id = await _create_trip(client, passenger_token)
        offer_id = await _make_offer(client, driver_token, trip_id)

        resp = await client.post(
            f"/api/v1/trips/{trip_id}/accept-offer",
            json={"offer_id": offer_id},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "accepted"
        assert data["final_price"] == "7.50"
