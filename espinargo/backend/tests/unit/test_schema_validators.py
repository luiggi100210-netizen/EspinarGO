"""
Tests unitarios para los validators de campos en schemas Pydantic.

Cubre: TripRequest, TripOfferRequest, UpdateTripStatusRequest,
PackageRequest, UpdatePackageStatusRequest, AdminDriverReviewRequest.
Todos son tests puros sin DB ni HTTP.
"""

import pytest
from pydantic import ValidationError

from app.schemas.trip import TripRequest, TripOfferRequest, UpdateTripStatusRequest
from app.schemas.package import PackageRequest, UpdatePackageStatusRequest
from app.schemas.admin import AdminDriverReviewRequest


# =============================================================================
# Helpers
# =============================================================================

_TRIP_BASE = {
    "origin_address": "Plaza de Armas, Espinar",
    "origin_lat": "-14.832",
    "origin_lng": "-71.013",
    "dest_address": "Mercado Central",
    "dest_lat": "-14.835",
    "dest_lng": "-71.010",
    "proposed_price": "8.00",
    "payment_method": "cash",
}

_PACKAGE_BASE = {
    "recipient_name": "Ana Torres",
    "recipient_phone": "+51987654321",
    "delivery_address": "Jr. Cusco 123, Espinar",
    "size": "small",
    "description": "Libros de texto",
    "is_fragile": False,
    "payment_method": "cash",
}


# =============================================================================
# TripRequest
# =============================================================================


class TestTripRequestSchema:

    def test_valid_trip_parsed(self):
        """TripRequest válido se parsea correctamente."""
        trip = TripRequest(**_TRIP_BASE)
        assert trip.proposed_price == "8.00"
        assert trip.payment_method == "cash"

    def test_invalid_coordinate_raises(self):
        """Coordenada no numérica → ValidationError."""
        with pytest.raises(ValidationError, match="Coordenada"):
            TripRequest(**{**_TRIP_BASE, "origin_lat": "no-es-numero"})

    def test_all_coordinates_validated(self):
        """Los cuatro campos de coordenada se validan."""
        for field in ["origin_lat", "origin_lng", "dest_lat", "dest_lng"]:
            with pytest.raises(ValidationError):
                TripRequest(**{**_TRIP_BASE, field: "abc"})

    def test_integer_coordinate_accepted(self):
        """Coordenada como entero string es válida."""
        trip = TripRequest(**{**_TRIP_BASE, "origin_lat": "-15"})
        assert trip.origin_lat == "-15"

    def test_proposed_price_formatted(self):
        """El precio propuesto se formatea a 2 decimales."""
        trip = TripRequest(**{**_TRIP_BASE, "proposed_price": "8"})
        assert trip.proposed_price == "8.00"

    def test_invalid_price_raises(self):
        """Precio inválido (0) → ValidationError."""
        with pytest.raises(ValidationError):
            TripRequest(**{**_TRIP_BASE, "proposed_price": "0"})

    def test_price_above_max_raises(self):
        """Precio > 999 → ValidationError."""
        with pytest.raises(ValidationError):
            TripRequest(**{**_TRIP_BASE, "proposed_price": "1000"})

    def test_invalid_payment_method_raises(self):
        """Método de pago desconocido → ValidationError."""
        with pytest.raises(ValidationError):
            TripRequest(**{**_TRIP_BASE, "payment_method": "bitcoin"})

    def test_valid_payment_methods(self):
        """Los tres métodos de pago válidos son aceptados."""
        for method in ["cash", "yape", "plin"]:
            trip = TripRequest(**{**_TRIP_BASE, "payment_method": method})
            assert trip.payment_method == method

    def test_origin_address_max_length(self):
        """Dirección de más de 300 chars → ValidationError."""
        with pytest.raises(ValidationError):
            TripRequest(**{**_TRIP_BASE, "origin_address": "A" * 301})

    def test_dest_address_max_length(self):
        """Destino de más de 300 chars → ValidationError."""
        with pytest.raises(ValidationError):
            TripRequest(**{**_TRIP_BASE, "dest_address": "B" * 301})

    def test_missing_required_field_raises(self):
        """Campo obligatorio faltante → ValidationError."""
        data = {k: v for k, v in _TRIP_BASE.items() if k != "origin_address"}
        with pytest.raises(ValidationError):
            TripRequest(**data)


# =============================================================================
# TripOfferRequest
# =============================================================================


class TestTripOfferRequestSchema:

    def test_valid_offer_parsed(self):
        """Oferta válida se parsea correctamente."""
        import uuid
        offer = TripOfferRequest(
            trip_id=uuid.uuid4(),
            offered_price="7.50",
        )
        assert offer.offered_price == "7.50"

    def test_price_formatted(self):
        """Precio se formatea a 2 decimales."""
        import uuid
        offer = TripOfferRequest(trip_id=uuid.uuid4(), offered_price="7")
        assert offer.offered_price == "7.00"

    def test_price_zero_raises(self):
        """Precio 0 → ValidationError."""
        import uuid
        with pytest.raises(ValidationError):
            TripOfferRequest(trip_id=uuid.uuid4(), offered_price="0")

    def test_price_negative_raises(self):
        """Precio negativo → ValidationError."""
        import uuid
        with pytest.raises(ValidationError):
            TripOfferRequest(trip_id=uuid.uuid4(), offered_price="-1")

    def test_message_optional(self):
        """Mensaje es opcional."""
        import uuid
        offer = TripOfferRequest(trip_id=uuid.uuid4(), offered_price="5.00")
        assert offer.message is None

    def test_message_max_length(self):
        """Mensaje de más de 200 chars → ValidationError."""
        import uuid
        with pytest.raises(ValidationError):
            TripOfferRequest(
                trip_id=uuid.uuid4(),
                offered_price="5.00",
                message="X" * 201,
            )

    def test_message_exactly_200_chars_accepted(self):
        """Mensaje de exactamente 200 chars es aceptado."""
        import uuid
        offer = TripOfferRequest(
            trip_id=uuid.uuid4(),
            offered_price="5.00",
            message="X" * 200,
        )
        assert len(offer.message) == 200

    def test_invalid_trip_id_raises(self):
        """trip_id que no es UUID → ValidationError."""
        with pytest.raises(ValidationError):
            TripOfferRequest(trip_id="no-es-uuid", offered_price="5.00")


# =============================================================================
# UpdateTripStatusRequest
# =============================================================================


class TestUpdateTripStatusRequestSchema:

    def test_valid_status_accepted(self):
        """Todos los estados válidos son aceptados."""
        valid = ["searching", "negotiating", "accepted", "in_progress", "completed", "cancelled"]
        for s in valid:
            req = UpdateTripStatusRequest(status=s)
            assert req.status == s

    def test_invalid_status_raises(self):
        """Estado desconocido → ValidationError."""
        with pytest.raises(ValidationError):
            UpdateTripStatusRequest(status="finished")

    def test_status_case_sensitive(self):
        """El estado es sensible a mayúsculas."""
        with pytest.raises(ValidationError):
            UpdateTripStatusRequest(status="Cancelled")

    def test_cancel_reason_optional(self):
        """cancel_reason es opcional."""
        req = UpdateTripStatusRequest(status="cancelled")
        assert req.cancel_reason is None

    def test_cancel_reason_provided(self):
        """Se puede proporcionar cancel_reason."""
        req = UpdateTripStatusRequest(status="cancelled", cancel_reason="no quiero")
        assert req.cancel_reason == "no quiero"

    def test_missing_status_raises(self):
        """Status faltante → ValidationError."""
        with pytest.raises(ValidationError):
            UpdateTripStatusRequest()


# =============================================================================
# PackageRequest
# =============================================================================


class TestPackageRequestSchema:

    def test_valid_package_parsed(self):
        """PackageRequest válido se parsea correctamente."""
        pkg = PackageRequest(**_PACKAGE_BASE)
        assert pkg.recipient_name == "Ana Torres"
        assert pkg.size == "small"

    def test_valid_sizes(self):
        """Los cuatro tamaños válidos son aceptados."""
        for size in ["envelope", "small", "medium", "large"]:
            pkg = PackageRequest(**{**_PACKAGE_BASE, "size": size})
            assert pkg.size == size

    def test_invalid_size_raises(self):
        """Tamaño desconocido → ValidationError."""
        with pytest.raises(ValidationError):
            PackageRequest(**{**_PACKAGE_BASE, "size": "extra_large"})

    def test_phone_normalized(self):
        """Teléfono de 9 dígitos se normaliza a +51XXXXXXXXX."""
        pkg = PackageRequest(**{**_PACKAGE_BASE, "recipient_phone": "987654321"})
        assert pkg.recipient_phone == "+51987654321"

    def test_invalid_phone_raises(self):
        """Teléfono no peruano → ValidationError."""
        with pytest.raises(ValidationError):
            PackageRequest(**{**_PACKAGE_BASE, "recipient_phone": "+15551234567"})

    def test_valid_payment_methods(self):
        """Métodos de pago válidos son aceptados."""
        for method in ["cash", "yape", "plin"]:
            pkg = PackageRequest(**{**_PACKAGE_BASE, "payment_method": method})
            assert pkg.payment_method == method

    def test_invalid_payment_raises(self):
        """Método de pago inválido → ValidationError."""
        with pytest.raises(ValidationError):
            PackageRequest(**{**_PACKAGE_BASE, "payment_method": "transferencia"})

    def test_recipient_name_max_length(self):
        """Nombre > 150 chars → ValidationError."""
        with pytest.raises(ValidationError):
            PackageRequest(**{**_PACKAGE_BASE, "recipient_name": "N" * 151})

    def test_delivery_address_max_length(self):
        """Dirección > 300 chars → ValidationError."""
        with pytest.raises(ValidationError):
            PackageRequest(**{**_PACKAGE_BASE, "delivery_address": "D" * 301})

    def test_description_max_length(self):
        """Descripción > 500 chars → ValidationError."""
        with pytest.raises(ValidationError):
            PackageRequest(**{**_PACKAGE_BASE, "description": "X" * 501})

    def test_is_fragile_defaults_to_false(self):
        """is_fragile tiene valor por defecto False."""
        data = {k: v for k, v in _PACKAGE_BASE.items() if k != "is_fragile"}
        pkg = PackageRequest(**data)
        assert pkg.is_fragile is False

    def test_is_fragile_true_accepted(self):
        """is_fragile=True es aceptado."""
        pkg = PackageRequest(**{**_PACKAGE_BASE, "is_fragile": True})
        assert pkg.is_fragile is True

    def test_missing_required_field_raises(self):
        """Campo obligatorio faltante → ValidationError."""
        data = {k: v for k, v in _PACKAGE_BASE.items() if k != "recipient_name"}
        with pytest.raises(ValidationError):
            PackageRequest(**data)


# =============================================================================
# UpdatePackageStatusRequest
# =============================================================================


class TestUpdatePackageStatusRequestSchema:

    def test_valid_statuses_accepted(self):
        """Los estados válidos son aceptados."""
        for s in ["picked_up", "in_transit", "delivered"]:
            req = UpdatePackageStatusRequest(status=s)
            assert req.status == s

    def test_invalid_status_raises(self):
        """Estado inválido → ValidationError."""
        with pytest.raises(ValidationError):
            UpdatePackageStatusRequest(status="pending")

    def test_assigned_status_raises(self):
        """'assigned' no es un estado de actualización válido → ValidationError."""
        with pytest.raises(ValidationError):
            UpdatePackageStatusRequest(status="assigned")

    def test_description_optional(self):
        """Descripción es opcional."""
        req = UpdatePackageStatusRequest(status="picked_up")
        assert req.description is None

    def test_description_provided(self):
        """Se puede proporcionar descripción."""
        req = UpdatePackageStatusRequest(
            status="picked_up",
            description="Recogido en domicilio",
        )
        assert req.description == "Recogido en domicilio"

    def test_description_max_length(self):
        """Descripción > 300 chars → ValidationError."""
        with pytest.raises(ValidationError):
            UpdatePackageStatusRequest(status="picked_up", description="X" * 301)

    def test_description_exactly_300_accepted(self):
        """Descripción de exactamente 300 chars es aceptada."""
        req = UpdatePackageStatusRequest(status="picked_up", description="X" * 300)
        assert len(req.description) == 300

    def test_missing_status_raises(self):
        """Status faltante → ValidationError."""
        with pytest.raises(ValidationError):
            UpdatePackageStatusRequest()


# =============================================================================
# AdminDriverReviewRequest
# =============================================================================


class TestAdminDriverReviewRequestSchema:

    def test_approve_action_accepted(self):
        """action='approve' es válido."""
        req = AdminDriverReviewRequest(action="approve")
        assert req.action == "approve"

    def test_reject_action_accepted(self):
        """action='reject' es válido."""
        req = AdminDriverReviewRequest(action="reject", rejection_reason="Documentos incompletos")
        assert req.action == "reject"

    def test_invalid_action_raises(self):
        """Acción desconocida → ValidationError."""
        with pytest.raises(ValidationError, match="approve.*reject"):
            AdminDriverReviewRequest(action="delete")

    def test_action_case_sensitive(self):
        """La acción es sensible a mayúsculas."""
        with pytest.raises(ValidationError):
            AdminDriverReviewRequest(action="Approve")

    def test_rejection_reason_optional(self):
        """rejection_reason es opcional."""
        req = AdminDriverReviewRequest(action="approve")
        assert req.rejection_reason is None

    def test_rejection_reason_max_length(self):
        """rejection_reason > 500 chars → ValidationError."""
        with pytest.raises(ValidationError):
            AdminDriverReviewRequest(action="reject", rejection_reason="X" * 501)

    def test_rejection_reason_exactly_500_accepted(self):
        """rejection_reason de exactamente 500 chars es aceptado."""
        req = AdminDriverReviewRequest(action="reject", rejection_reason="X" * 500)
        assert len(req.rejection_reason) == 500

    def test_missing_action_raises(self):
        """action faltante → ValidationError."""
        with pytest.raises(ValidationError):
            AdminDriverReviewRequest()
