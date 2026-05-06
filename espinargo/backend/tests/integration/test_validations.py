"""
Tests de integración para validaciones de entrada.

Cubre paths de error que no requieren Cloudinary:
- Document upload: tipo inválido, content-type incorrecto, acceso no autorizado
- Avatar upload: content-type incorrecto, acceso no autorizado
- Trips: activo inexistente, ofertas inválidas
- Ratings: score fuera de rango, viaje ajeno
- Packages: creación sin auth, transición inválida temprana
"""

import io
import pytest
from httpx import AsyncClient


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fake_image(filename: str = "test.jpg", content_type: str = "image/jpeg") -> tuple:
    return (filename, io.BytesIO(b"fake-image-data"), content_type)


def _fake_pdf(filename: str = "doc.pdf") -> tuple:
    return (filename, io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")


def _fake_text(filename: str = "hack.txt") -> tuple:
    return (filename, io.BytesIO(b"not an image"), "text/plain")


TRIP_DATA = {
    "origin_address": "Plaza de Armas",
    "origin_lat": "-14.832",
    "origin_lng": "-71.013",
    "dest_address": "Mercado Central",
    "dest_lat": "-14.835",
    "dest_lng": "-71.010",
    "proposed_price": "8.00",
    "payment_method": "cash",
}


# ── Document upload validations ────────────────────────────────────────────────

class TestDocumentUploadValidations:

    async def test_invalid_document_type_returns_400(
        self, client: AsyncClient, driver_token: str
    ):
        resp = await client.post(
            "/api/v1/users/me/documents/passport",
            files={"file": _fake_image()},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 400
        assert "inválido" in resp.json()["detail"].lower() or "invalid" in resp.json()["detail"].lower()

    async def test_document_wrong_content_type_returns_400(
        self, client: AsyncClient, driver_token: str
    ):
        resp = await client.post(
            "/api/v1/users/me/documents/dni_front",
            files={"file": _fake_text()},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 400

    async def test_passenger_cannot_upload_documents(
        self, client: AsyncClient, passenger_token: str
    ):
        resp = await client.post(
            "/api/v1/users/me/documents/dni_front",
            files={"file": _fake_image()},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 403

    async def test_document_upload_requires_auth(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/users/me/documents/dni_front",
            files={"file": _fake_image()},
        )
        assert resp.status_code == 401


# ── Avatar upload validations ──────────────────────────────────────────────────

class TestAvatarUploadValidations:

    async def test_avatar_wrong_content_type_returns_400(
        self, client: AsyncClient, passenger_token: str
    ):
        resp = await client.post(
            "/api/v1/users/me/avatar",
            files={"file": _fake_text()},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 400

    async def test_avatar_upload_requires_auth(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/users/me/avatar",
            files={"file": _fake_image()},
        )
        assert resp.status_code == 401


# ── Trips edge cases ───────────────────────────────────────────────────────────

class TestTripEdgeCases:

    async def test_trip_request_missing_required_field_returns_422(
        self, client: AsyncClient, passenger_token: str
    ):
        incomplete = {k: v for k, v in TRIP_DATA.items() if k != "dest_address"}
        resp = await client.post(
            "/api/v1/trips/",
            json=incomplete,
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 422

    async def test_offer_on_nonexistent_trip_returns_404(
        self, client: AsyncClient, driver_token: str
    ):
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.post(
            "/api/v1/trips/offer",
            json={"trip_id": fake_id, "offered_price": "7.50"},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 404

    async def test_accept_offer_on_nonexistent_trip_returns_404(
        self, client: AsyncClient, passenger_token: str
    ):
        fake_trip_id = "00000000-0000-0000-0000-000000000000"
        fake_offer_id = "00000000-0000-0000-0000-000000000001"
        resp = await client.post(
            f"/api/v1/trips/{fake_trip_id}/accept-offer",
            json={"offer_id": fake_offer_id},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 404

    async def test_unauthenticated_cannot_create_trip(self, client: AsyncClient):
        resp = await client.post("/api/v1/trips/", json=TRIP_DATA)
        assert resp.status_code == 401

    async def test_unauthenticated_cannot_get_history(self, client: AsyncClient):
        resp = await client.get("/api/v1/trips/history")
        assert resp.status_code == 401


# ── Ratings edge cases ─────────────────────────────────────────────────────────

class TestRatingEdgeCases:

    async def test_score_zero_rejected(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Score 0 está por debajo del mínimo (1)."""
        trip_resp = await client.post(
            "/api/v1/trips/", json=TRIP_DATA,
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        trip_id = trip_resp.json()["id"]

        resp = await client.post(
            "/api/v1/ratings/",
            json={"trip_id": trip_id, "score": 0},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 422

    async def test_rating_requires_auth(self, client: AsyncClient):
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.post(
            "/api/v1/ratings/",
            json={"trip_id": fake_id, "score": 5},
        )
        assert resp.status_code == 401

    async def test_received_ratings_requires_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/ratings/received")
        assert resp.status_code == 401


# ── Packages edge cases ────────────────────────────────────────────────────────

class TestPackageEdgeCases:

    async def test_create_package_requires_auth(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/packages/",
            json={
                "recipient_name": "Test",
                "recipient_phone": "+51987654321",
                "delivery_address": "Av. Test 1",
                "size": "small",
                "description": "Test",
                "is_fragile": False,
                "payment_method": "cash",
            },
        )
        assert resp.status_code == 401

    async def test_invalid_size_rejected(
        self, client: AsyncClient, passenger_token: str
    ):
        resp = await client.post(
            "/api/v1/packages/",
            json={
                "recipient_name": "Test",
                "recipient_phone": "+51987654321",
                "delivery_address": "Av. Test 1",
                "size": "gigantic",
                "description": "Test",
                "is_fragile": False,
                "payment_method": "cash",
            },
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 422

    async def test_assign_nonexistent_package_returns_404(
        self, client: AsyncClient, driver_token: str
    ):
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.post(
            f"/api/v1/packages/{fake_id}/assign",
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 404
