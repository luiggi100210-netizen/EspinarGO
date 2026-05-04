"""
Tests de integración para el flujo completo de viajes.
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


class TestTripFlow:

    async def test_passenger_creates_trip(self, client: AsyncClient, passenger_token: str):
        resp = await client.post(
            "/api/v1/trips/",
            json=TRIP_DATA,
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "searching"
        assert data["proposed_price"] == "8.00"

    async def test_driver_cannot_create_trip(self, client: AsyncClient, driver_token: str):
        resp = await client.post(
            "/api/v1/trips/",
            json=TRIP_DATA,
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 403

    async def test_passenger_gets_active_trip(self, client: AsyncClient, passenger_token: str):
        await client.post(
            "/api/v1/trips/",
            json=TRIP_DATA,
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        resp = await client.get(
            "/api/v1/trips/active",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200
        assert resp.json() is not None

    async def test_driver_makes_offer(self, client: AsyncClient, passenger_token: str, driver_token: str):
        trip_resp = await client.post(
            "/api/v1/trips/",
            json=TRIP_DATA,
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        trip_id = trip_resp.json()["id"]

        resp = await client.post(
            "/api/v1/trips/offer",
            json={"trip_id": trip_id, "offered_price": "7.50", "message": "Hola"},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["offered_price"] == "7.50"

    async def test_driver_cannot_offer_twice(self, client: AsyncClient, passenger_token: str, driver_token: str):
        trip_resp = await client.post(
            "/api/v1/trips/",
            json=TRIP_DATA,
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        trip_id = trip_resp.json()["id"]

        await client.post(
            "/api/v1/trips/offer",
            json={"trip_id": trip_id, "offered_price": "7.50"},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        resp = await client.post(
            "/api/v1/trips/offer",
            json={"trip_id": trip_id, "offered_price": "7.00"},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 400

    async def test_passenger_accepts_offer(self, client: AsyncClient, passenger_token: str, driver_token: str):
        trip_resp = await client.post(
            "/api/v1/trips/",
            json=TRIP_DATA,
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        trip_id = trip_resp.json()["id"]

        offer_resp = await client.post(
            "/api/v1/trips/offer",
            json={"trip_id": trip_id, "offered_price": "7.50"},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        offer_id = offer_resp.json()["id"]

        resp = await client.post(
            f"/api/v1/trips/{trip_id}/accept-offer",
            json={"offer_id": offer_id},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "accepted"
        assert resp.json()["final_price"] == "7.50"

    async def test_full_trip_lifecycle(self, client: AsyncClient, passenger_token: str, driver_token: str):
        trip_resp = await client.post(
            "/api/v1/trips/",
            json=TRIP_DATA,
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        trip_id = trip_resp.json()["id"]

        offer_resp = await client.post(
            "/api/v1/trips/offer",
            json={"trip_id": trip_id, "offered_price": "7.50"},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        offer_id = offer_resp.json()["id"]

        await client.post(
            f"/api/v1/trips/{trip_id}/accept-offer",
            json={"offer_id": offer_id},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )

        start_resp = await client.post(
            f"/api/v1/trips/{trip_id}/start",
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert start_resp.status_code == 200
        assert start_resp.json()["status"] == "in_progress"

        complete_resp = await client.post(
            f"/api/v1/trips/{trip_id}/complete",
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert complete_resp.status_code == 200
        assert complete_resp.json()["status"] == "completed"

    async def test_passenger_cancels_trip(self, client: AsyncClient, passenger_token: str):
        trip_resp = await client.post(
            "/api/v1/trips/",
            json=TRIP_DATA,
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        trip_id = trip_resp.json()["id"]

        resp = await client.post(
            f"/api/v1/trips/{trip_id}/cancel",
            json={"status": "cancelled"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"

    async def test_trip_history(self, client: AsyncClient, passenger_token: str, driver_token: str):
        trip_resp = await client.post(
            "/api/v1/trips/",
            json=TRIP_DATA,
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        trip_id = trip_resp.json()["id"]

        offer_resp = await client.post(
            "/api/v1/trips/offer",
            json={"trip_id": trip_id, "offered_price": "7.50"},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        offer_id = offer_resp.json()["id"]
        await client.post(
            f"/api/v1/trips/{trip_id}/accept-offer",
            json={"offer_id": offer_id},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        await client.post(f"/api/v1/trips/{trip_id}/start", headers={"Authorization": f"Bearer {driver_token}"})
        await client.post(f"/api/v1/trips/{trip_id}/complete", headers={"Authorization": f"Bearer {driver_token}"})

        resp = await client.get(
            "/api/v1/trips/history",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["meta"]["total"] >= 1

    async def test_cannot_start_without_accept(self, client: AsyncClient, passenger_token: str, driver_token: str):
        trip_resp = await client.post(
            "/api/v1/trips/",
            json=TRIP_DATA,
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        trip_id = trip_resp.json()["id"]

        resp = await client.post(
            f"/api/v1/trips/{trip_id}/start",
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code in (400, 403)
