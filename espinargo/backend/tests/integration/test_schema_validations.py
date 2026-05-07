"""
Tests de integración para validaciones de schema en todos los módulos.

Cubre los validadores de Pydantic que no están cubiertos en otros archivos:
precios, coordenadas, métodos de pago, longitudes máximas, formatos OTP,
asientos de vehículo, calificaciones, teléfonos de destinatario.
"""

import pytest
from httpx import AsyncClient


# ── Datos base ─────────────────────────────────────────────────────────────────

TRIP_BASE = {
    "origin_address": "Plaza de Armas",
    "origin_lat": "-14.832",
    "origin_lng": "-71.013",
    "dest_address": "Mercado Central",
    "dest_lat": "-14.835",
    "dest_lng": "-71.010",
    "proposed_price": "8.00",
    "payment_method": "cash",
}

PACKAGE_BASE = {
    "recipient_name": "María López",
    "recipient_phone": "+51987000002",
    "delivery_address": "Jr. Tacna 456",
    "size": "small",
    "description": "Documentos",
    "is_fragile": False,
    "payment_method": "cash",
}


# ── Viajes: precios ────────────────────────────────────────────────────────────

class TestTripPriceValidation:

    async def test_price_zero_rejected(self, client: AsyncClient, passenger_token: str):
        """Precio = 0 → 422."""
        resp = await client.post(
            "/api/v1/trips/",
            json={**TRIP_BASE, "proposed_price": "0"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 422

    async def test_price_negative_rejected(self, client: AsyncClient, passenger_token: str):
        """Precio negativo → 422."""
        resp = await client.post(
            "/api/v1/trips/",
            json={**TRIP_BASE, "proposed_price": "-5.00"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 422

    async def test_price_above_max_rejected(self, client: AsyncClient, passenger_token: str):
        """Precio > 999 → 422."""
        resp = await client.post(
            "/api/v1/trips/",
            json={**TRIP_BASE, "proposed_price": "1000"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 422

    async def test_price_non_numeric_rejected(self, client: AsyncClient, passenger_token: str):
        """Precio no numérico → 422."""
        resp = await client.post(
            "/api/v1/trips/",
            json={**TRIP_BASE, "proposed_price": "diez soles"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 422

    async def test_price_valid_integer_accepted(self, client: AsyncClient, passenger_token: str):
        """Precio como entero es aceptado (ej. '5' → '5.00')."""
        resp = await client.post(
            "/api/v1/trips/",
            json={**TRIP_BASE, "proposed_price": "5"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 201


# ── Viajes: coordenadas y otros campos ────────────────────────────────────────

class TestTripFieldValidation:

    async def test_invalid_lat_rejected(self, client: AsyncClient, passenger_token: str):
        """Coordenada no numérica → 422."""
        resp = await client.post(
            "/api/v1/trips/",
            json={**TRIP_BASE, "origin_lat": "sur"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 422

    async def test_invalid_lng_rejected(self, client: AsyncClient, passenger_token: str):
        """Longitud no numérica → 422."""
        resp = await client.post(
            "/api/v1/trips/",
            json={**TRIP_BASE, "dest_lng": "oeste"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 422

    async def test_invalid_payment_method_rejected(
        self, client: AsyncClient, passenger_token: str
    ):
        """Método de pago inválido → 422."""
        resp = await client.post(
            "/api/v1/trips/",
            json={**TRIP_BASE, "payment_method": "bitcoin"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 422

    async def test_yape_payment_accepted(self, client: AsyncClient, passenger_token: str):
        """Método de pago 'yape' es válido."""
        resp = await client.post(
            "/api/v1/trips/",
            json={**TRIP_BASE, "payment_method": "yape"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 201

    async def test_plin_payment_accepted(self, client: AsyncClient, passenger_token: str):
        """Método de pago 'plin' es válido."""
        resp = await client.post(
            "/api/v1/trips/",
            json={**TRIP_BASE, "payment_method": "plin"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 201

    async def test_origin_address_too_long_rejected(
        self, client: AsyncClient, passenger_token: str
    ):
        """Dirección de origen > 300 chars → 422."""
        resp = await client.post(
            "/api/v1/trips/",
            json={**TRIP_BASE, "origin_address": "A" * 301},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 422


# ── Viajes: ofertas ────────────────────────────────────────────────────────────

class TestOfferPriceValidation:

    async def _create_trip(self, client, passenger_token):
        resp = await client.post(
            "/api/v1/trips/", json=TRIP_BASE,
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        return resp.json()["id"]

    async def test_offer_price_zero_rejected(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Precio de oferta = 0 → 422."""
        trip_id = await self._create_trip(client, passenger_token)
        resp = await client.post(
            "/api/v1/trips/offer",
            json={"trip_id": trip_id, "offered_price": "0"},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 422

    async def test_offer_price_negative_rejected(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Precio de oferta negativo → 422."""
        trip_id = await self._create_trip(client, passenger_token)
        resp = await client.post(
            "/api/v1/trips/offer",
            json={"trip_id": trip_id, "offered_price": "-1"},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 422

    async def test_offer_message_too_long_rejected(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Mensaje de oferta > 200 chars → 422."""
        trip_id = await self._create_trip(client, passenger_token)
        resp = await client.post(
            "/api/v1/trips/offer",
            json={"trip_id": trip_id, "offered_price": "7.00", "message": "M" * 201},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 422


# ── Encomiendas: validaciones de campos ───────────────────────────────────────

class TestPackageFieldValidation:

    async def test_invalid_recipient_phone_rejected(
        self, client: AsyncClient, passenger_token: str
    ):
        """Teléfono de destinatario no peruano → 422."""
        resp = await client.post(
            "/api/v1/packages/",
            json={**PACKAGE_BASE, "recipient_phone": "+1555000000"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 422

    async def test_invalid_payment_method_rejected(
        self, client: AsyncClient, passenger_token: str
    ):
        """Método de pago inválido en encomienda → 422."""
        resp = await client.post(
            "/api/v1/packages/",
            json={**PACKAGE_BASE, "payment_method": "transferencia"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 422

    async def test_description_too_long_rejected(
        self, client: AsyncClient, passenger_token: str
    ):
        """Descripción > 500 chars → 422."""
        resp = await client.post(
            "/api/v1/packages/",
            json={**PACKAGE_BASE, "description": "X" * 501},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 422

    async def test_recipient_name_too_long_rejected(
        self, client: AsyncClient, passenger_token: str
    ):
        """Nombre de destinatario > 150 chars → 422."""
        resp = await client.post(
            "/api/v1/packages/",
            json={**PACKAGE_BASE, "recipient_name": "N" * 151},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 422

    async def test_delivery_address_too_long_rejected(
        self, client: AsyncClient, passenger_token: str
    ):
        """Dirección de entrega > 300 chars → 422."""
        resp = await client.post(
            "/api/v1/packages/",
            json={**PACKAGE_BASE, "delivery_address": "D" * 301},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 422

    async def test_yape_payment_in_package_accepted(
        self, client: AsyncClient, passenger_token: str
    ):
        """Método de pago 'yape' es válido en encomiendas."""
        resp = await client.post(
            "/api/v1/packages/",
            json={**PACKAGE_BASE, "payment_method": "yape", "recipient_phone": "+51987000003"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 201

    async def test_update_status_description_too_long_rejected(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Descripción de tracking > 300 chars → 422."""
        create = await client.post(
            "/api/v1/packages/", json=PACKAGE_BASE,
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        pkg_id = create.json()["id"]
        await client.post(
            f"/api/v1/packages/{pkg_id}/assign",
            headers={"Authorization": f"Bearer {driver_token}"},
        )

        resp = await client.post(
            f"/api/v1/packages/{pkg_id}/update-status",
            json={"status": "picked_up", "description": "D" * 301},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 422


# ── Auth: validaciones de OTP y nombre ────────────────────────────────────────

class TestAuthSchemaValidation:

    async def test_full_name_too_short_rejected(self, client: AsyncClient):
        """full_name de 1 char → 422 (min_length=2)."""
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "A",
                "phone_number": "+51900002001",
                "password": "pass1234",
                "role": "passenger",
            },
        )
        assert resp.status_code == 422

    async def test_full_name_too_long_rejected(self, client: AsyncClient):
        """full_name de 151 chars → 422 (max_length=150)."""
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "A" * 151,
                "phone_number": "+51900002002",
                "password": "pass1234",
                "role": "passenger",
            },
        )
        assert resp.status_code == 422

    async def test_otp_code_with_letters_rejected(self, client: AsyncClient):
        """Código OTP con letras → 422."""
        resp = await client.post(
            "/api/v1/auth/verify-phone",
            json={
                "phone_number": "+51900000001",
                "code": "ABCDEF",
            },
        )
        assert resp.status_code == 422

    async def test_otp_code_too_short_rejected(self, client: AsyncClient):
        """Código OTP de 5 dígitos → 422 (requiere exactamente 6)."""
        resp = await client.post(
            "/api/v1/auth/verify-phone",
            json={
                "phone_number": "+51900000001",
                "code": "12345",
            },
        )
        assert resp.status_code == 422

    async def test_otp_code_too_long_rejected(self, client: AsyncClient):
        """Código OTP de 7 dígitos → 422."""
        resp = await client.post(
            "/api/v1/auth/verify-phone",
            json={
                "phone_number": "+51900000001",
                "code": "1234567",
            },
        )
        assert resp.status_code == 422

    async def test_send_otp_invalid_purpose_rejected(self, client: AsyncClient):
        """Propósito OTP inválido → 422."""
        resp = await client.post(
            "/api/v1/auth/send-otp",
            json={"phone_number": "+51900000001", "purpose": "hack"},
        )
        assert resp.status_code == 422

    async def test_reset_password_non_digit_otp_rejected(self, client: AsyncClient):
        """OTP con letras en reset-password → 422."""
        resp = await client.post(
            "/api/v1/auth/reset-password",
            json={
                "phone_number": "+51900000001",
                "otp_code": "ABCDEF",
                "new_password": "nuevaClave123",
            },
        )
        assert resp.status_code == 422

    async def test_reset_password_too_short_new_password_rejected(
        self, client: AsyncClient
    ):
        """Nueva contraseña < 6 chars en reset → 422."""
        resp = await client.post(
            "/api/v1/auth/reset-password",
            json={
                "phone_number": "+51900000001",
                "otp_code": "123456",
                "new_password": "abc",
            },
        )
        assert resp.status_code == 422


# ── Usuarios: validaciones de vehículo y perfil ───────────────────────────────

class TestUserSchemaValidation:

    async def test_update_profile_name_too_short_rejected(
        self, client: AsyncClient, passenger_token: str
    ):
        """full_name de 1 char en PATCH /me → 422."""
        resp = await client.patch(
            "/api/v1/users/me",
            json={"full_name": "X"},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 422

    async def test_vehicle_seats_zero_rejected(
        self, client: AsyncClient, driver_token: str
    ):
        """vehicle_seats = 0 → 422 (mín 1)."""
        resp = await client.patch(
            "/api/v1/users/me/vehicle",
            json={"vehicle_seats": 0},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 422

    async def test_vehicle_seats_above_max_rejected(
        self, client: AsyncClient, driver_token: str
    ):
        """vehicle_seats = 7 → 422 (máx 6)."""
        resp = await client.patch(
            "/api/v1/users/me/vehicle",
            json={"vehicle_seats": 7},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 422

    async def test_vehicle_seats_max_valid(
        self, client: AsyncClient, driver_token: str
    ):
        """vehicle_seats = 6 es válido."""
        resp = await client.patch(
            "/api/v1/users/me/vehicle",
            json={"vehicle_seats": 6},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 200

    async def test_vehicle_seats_min_valid(
        self, client: AsyncClient, driver_token: str
    ):
        """vehicle_seats = 1 es válido."""
        resp = await client.patch(
            "/api/v1/users/me/vehicle",
            json={"vehicle_seats": 1},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 200

    async def test_vehicle_plate_normalized_to_uppercase(
        self, client: AsyncClient, driver_token: str
    ):
        """La placa se normaliza a mayúsculas automáticamente."""
        resp = await client.patch(
            "/api/v1/users/me/vehicle",
            json={"vehicle_plate": "abc-123"},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["vehicle_plate"] == "ABC-123"


# ── Calificaciones: validaciones ───────────────────────────────────────────────

class TestRatingSchemaValidation:

    async def test_comment_too_long_rejected(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Comentario > 500 chars → 422."""
        # Crear y completar un viaje
        trip = await client.post(
            "/api/v1/trips/", json=TRIP_BASE,
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        trip_id = trip.json()["id"]

        offer = await client.post(
            "/api/v1/trips/offer",
            json={"trip_id": trip_id, "offered_price": "7.00"},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        offer_id = offer.json()["id"]

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

        resp = await client.post(
            "/api/v1/ratings/",
            json={"trip_id": trip_id, "score": 5, "comment": "C" * 501},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 422

    async def test_score_boundary_1_accepted(
        self, client: AsyncClient, passenger_token: str, driver_token: str
    ):
        """Score = 1 (mínimo válido) es aceptado."""
        trip = await client.post(
            "/api/v1/trips/", json=TRIP_BASE,
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        trip_id = trip.json()["id"]

        offer = await client.post(
            "/api/v1/trips/offer",
            json={"trip_id": trip_id, "offered_price": "7.00"},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        offer_id = offer.json()["id"]

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

        resp = await client.post(
            "/api/v1/ratings/",
            json={"trip_id": trip_id, "score": 1},
            headers={"Authorization": f"Bearer {passenger_token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["score"] == 1
