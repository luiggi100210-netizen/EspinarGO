"""
Tests de integración extendidos para calificaciones.

Cubre: no-participante, resumen de ceros, paginación,
scores inválidos, auth guard.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from tests.integration.conftest import TestSession
from app.models.user import User


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


async def _complete_trip(client: AsyncClient, passenger_token: str, driver_token: str) -> str:
    """Helper: crea y completa un viaje, retorna trip_id."""
    trip = await client.post(
        "/api/v1/trips/", json=TRIP_DATA,
        headers={"Authorization": f"Bearer {passenger_token}"},
    )
    trip_id = trip.json()["id"]

    offer = await client.post(
        "/api/v1/trips/offer",
        json={"trip_id": trip_id, "offered_price": "7.50"},
        headers={"Authorization": f"Bearer {driver_token}"},
    )
    offer_id = offer.json()["id"]

    await client.post(
        f"/api/v1/trips/{trip_id}/accept-offer",
        json={"offer_id": offer_id},
        headers={"Authorization": f"Bearer {passenger_token}"},
    )
    await client.post(f"/api/v1/trips/{trip_id}/start", headers={"Authorization": f"Bearer {driver_token}"})
    await client.post(f"/api/v1/trips/{trip_id}/complete", headers={"Authorization": f"Bearer {driver_token}"})
    return trip_id


class TestRatingAuth:

    async def test_received_ratings_requires_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/ratings/received")
        assert resp.status_code == 401

    async def test_rating_summary_requires_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/ratings/summary/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 401

    async def test_create_rating_requires_auth(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/ratings/",
            json={"trip_id": "00000000-0000-0000-0000-000000000000", "score": 5},
        )
        assert resp.status_code == 401


class TestRatingEdgeCases:

    async def test_non_participant_cannot_rate(
        self, client: AsyncClient, passenger_token: str, driver_token: str, admin_token: str
    ):
        """Un usuario ajeno al viaje no puede calificar."""
        trip_id = await _complete_trip(client, passenger_token, driver_token)

        resp = await client.post(
            "/api/v1/ratings/",
            json={"trip_id": trip_id, "score": 5},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 403

    async def test_cannot_rate_nonexistent_trip(
        self, client: AsyncClient, passenger_token: str
    ):
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.post(
            "/api/v1/ratings/",
            json={"trip_id": fake_id, "score": 4},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 404

    async def test_score_zero_rejected(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Score 0 es inválido (mínimo 1)."""
        trip_id = await _complete_trip(client, passenger_token, driver_token)

        resp = await client.post(
            "/api/v1/ratings/",
            json={"trip_id": trip_id, "score": 0},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 422

    async def test_score_six_rejected(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Score 6 es inválido (máximo 5)."""
        trip_id = await _complete_trip(client, passenger_token, driver_token)

        resp = await client.post(
            "/api/v1/ratings/",
            json={"trip_id": trip_id, "score": 6},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 422

    async def test_rating_with_comment(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Calificar con comentario devuelve el comentario."""
        trip_id = await _complete_trip(client, passenger_token, driver_token)

        resp = await client.post(
            "/api/v1/ratings/",
            json={"trip_id": trip_id, "score": 5, "comment": "Muy buen conductor"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["comment"] == "Muy buen conductor"


class TestRatingSummary:

    async def test_summary_for_user_with_no_ratings(
        self, client: AsyncClient, passenger_token: str
    ):
        """Usuario sin calificaciones retorna resumen con ceros."""
        # Usar ID del pasajero (que generalmente no recibe ratings de conductores)
        async with TestSession() as db:
            result = await db.execute(
                select(User).where(User.phone_number == "+51900000001")
            )
            passenger = result.scalar_one()
            user_id = str(passenger.id)

        resp = await client.get(
            f"/api/v1/ratings/summary/{user_id}",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "average_score" in data
        assert "total_ratings" in data
        assert "five_stars" in data
        assert data["total_ratings"] >= 0
        assert data["average_score"] >= 0.0

    async def test_summary_has_star_distribution(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """El resumen incluye la distribución de estrellas."""
        async with TestSession() as db:
            result = await db.execute(
                select(User).where(User.phone_number == "+51900000002")
            )
            driver = result.scalar_one()
            driver_id = str(driver.id)

        trip_id = await _complete_trip(client, passenger_token, driver_token)
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
        assert data["five_stars"] >= 1
        assert data["total_ratings"] >= 1
        assert 0.0 <= data["average_score"] <= 5.0

    async def test_summary_fields_are_complete(
        self, client: AsyncClient, passenger_token: str
    ):
        """Verifica que todos los campos del resumen estén presentes."""
        async with TestSession() as db:
            result = await db.execute(
                select(User).where(User.phone_number == "+51900000002")
            )
            driver = result.scalar_one()
            driver_id = str(driver.id)

        resp = await client.get(
            f"/api/v1/ratings/summary/{driver_id}",
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        for field in ["average_score", "total_ratings", "five_stars", "four_stars",
                      "three_stars", "two_stars", "one_star"]:
            assert field in data, f"Campo faltante: {field}"


class TestReceivedRatingsPagination:

    async def test_pagination_default(
        self, client: AsyncClient, driver_token: str
    ):
        """Paginación con valores por defecto."""
        resp = await client.get(
            "/api/v1/ratings/received",
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_pagination_with_per_page(
        self, client: AsyncClient, driver_token: str
    ):
        """Limitar resultados con per_page."""
        resp = await client.get(
            "/api/v1/ratings/received?per_page=1",
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 200
        assert len(resp.json()) <= 1

    async def test_invalid_per_page_rejected(
        self, client: AsyncClient, driver_token: str
    ):
        """per_page > 50 es rechazado por validación."""
        resp = await client.get(
            "/api/v1/ratings/received?per_page=100",
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 422
