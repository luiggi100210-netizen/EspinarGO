"""
Tests de integración para el sistema de calificaciones.
"""

import pytest
from httpx import AsyncClient

from tests.integration.conftest import TestSession


TRIP_DATA = {
    "origin_address": "Plaza de Armas, Espinar",
    "origin_lat": -14.832,
    "origin_lng": -71.013,
    "dest_address": "Mercado Central",
    "dest_lat": -14.835,
    "dest_lng": -71.010,
    "proposed_price": "8.00",
    "payment_method": "cash",
}


async def complete_trip(client: AsyncClient, passenger_token: str, driver_token: str) -> str:
    """Helper: crea y completa un viaje, retorna trip_id."""
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

    return trip_id


class TestRatings:

    async def test_passenger_rates_driver(self, client: AsyncClient, passenger_token: str, driver_token: str):
        trip_id = await complete_trip(client, passenger_token, driver_token)

        resp = await client.post(
            "/api/v1/ratings/",
            json={"trip_id": trip_id, "score": 5, "comment": "Excelente conductor"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["score"] == 5
        assert data["rating_type"] == "passenger_to_driver"

    async def test_driver_rates_passenger(self, client: AsyncClient, passenger_token: str, driver_token: str):
        trip_id = await complete_trip(client, passenger_token, driver_token)

        resp = await client.post(
            "/api/v1/ratings/",
            json={"trip_id": trip_id, "score": 4, "comment": "Buen pasajero"},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["rating_type"] == "driver_to_passenger"

    async def test_cannot_rate_twice(self, client: AsyncClient, passenger_token: str, driver_token: str):
        trip_id = await complete_trip(client, passenger_token, driver_token)

        await client.post(
            "/api/v1/ratings/",
            json={"trip_id": trip_id, "score": 5},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        resp = await client.post(
            "/api/v1/ratings/",
            json={"trip_id": trip_id, "score": 3},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 400

    async def test_cannot_rate_incomplete_trip(self, client: AsyncClient, passenger_token: str):
        trip_resp = await client.post(
            "/api/v1/trips/",
            json=TRIP_DATA,
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        trip_id = trip_resp.json()["id"]

        resp = await client.post(
            "/api/v1/ratings/",
            json={"trip_id": trip_id, "score": 5},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 400

    async def test_invalid_score_rejected(self, client: AsyncClient, passenger_token: str, driver_token: str):
        trip_id = await complete_trip(client, passenger_token, driver_token)

        resp = await client.post(
            "/api/v1/ratings/",
            json={"trip_id": trip_id, "score": 6},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 422

    async def test_get_received_ratings(self, client: AsyncClient, passenger_token: str, driver_token: str):
        trip_id = await complete_trip(client, passenger_token, driver_token)

        await client.post(
            "/api/v1/ratings/",
            json={"trip_id": trip_id, "score": 5},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )

        resp = await client.get(
            "/api/v1/ratings/received",
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 200
        ratings = resp.json()
        assert len(ratings) >= 1
        assert ratings[0]["rating_type"] == "passenger_to_driver"

    async def test_rating_updates_driver_profile(self, client: AsyncClient, passenger_token: str, driver_token: str):
        from sqlalchemy import select
        from app.models.user import User, DriverProfile

        async with TestSession() as db:
            result = await db.execute(select(User).where(User.phone_number == "+51900000002"))
            driver = result.scalar_one()
            dp_before = driver.driver_profile
            rating_before = dp_before.rating
            count_before = dp_before.rating_count

        trip_id = await complete_trip(client, passenger_token, driver_token)
        await client.post(
            "/api/v1/ratings/",
            json={"trip_id": trip_id, "score": 4},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )

        async with TestSession() as db:
            result = await db.execute(select(User).where(User.phone_number == "+51900000002"))
            driver = result.scalar_one()
            dp_after = driver.driver_profile
            assert dp_after.rating_count == count_before + 1
            assert dp_after.rating != rating_before or count_before == 0

    async def test_rating_summary(self, client: AsyncClient, passenger_token: str, driver_token: str):
        from sqlalchemy import select
        from app.models.user import User

        async with TestSession() as db:
            result = await db.execute(select(User).where(User.phone_number == "+51900000002"))
            driver = result.scalar_one()
            driver_id = str(driver.id)

        trip_id = await complete_trip(client, passenger_token, driver_token)
        await client.post(
            "/api/v1/ratings/",
            json={"trip_id": trip_id, "score": 5},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )

        resp = await client.get(
            f"/api/v1/ratings/summary/{driver_id}",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_ratings"] >= 1
        assert 0.0 <= data["average_score"] <= 5.0
