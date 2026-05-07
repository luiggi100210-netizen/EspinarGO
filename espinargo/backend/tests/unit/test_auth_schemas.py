"""
Tests unitarios para los schemas de autenticación.

Cubre: RegisterRequest (full_name normalización, rol, teléfono, contraseña),
SendOTPRequest (propósito), VerifyOTPRequest (código dígitos),
LoginRequest (teléfono), UpdateProfileRequest (full_name normalización),
UpdateVehicleRequest (tipo, año, placa, asientos).

Sin DB ni HTTP — tests de validación Pydantic puros.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.schemas.auth import (
    RegisterRequest,
    SendOTPRequest,
    VerifyOTPRequest,
    LoginRequest,
)
from app.schemas.user import UpdateProfileRequest, UpdateVehicleRequest


# =============================================================================
# RegisterRequest
# =============================================================================

_REGISTER_BASE = {
    "full_name": "Juan Quispe",
    "phone_number": "+51987654321",
    "password": "pass1234",
    "role": "passenger",
}


class TestRegisterRequestSchema:

    def test_valid_passenger_parsed(self):
        """Registro de pasajero válido se parsea correctamente."""
        req = RegisterRequest(**_REGISTER_BASE)
        assert req.role == "passenger"

    def test_valid_driver_parsed(self):
        """Registro de conductor válido se parsea correctamente."""
        req = RegisterRequest(**{**_REGISTER_BASE, "role": "driver"})
        assert req.role == "driver"

    def test_invalid_role_raises(self):
        """Rol desconocido → ValidationError."""
        with pytest.raises(ValidationError, match="passenger.*driver|driver.*passenger"):
            RegisterRequest(**{**_REGISTER_BASE, "role": "admin"})

    def test_admin_role_raises(self):
        """Rol 'admin' no está permitido en registro → ValidationError."""
        with pytest.raises(ValidationError):
            RegisterRequest(**{**_REGISTER_BASE, "role": "admin"})

    def test_full_name_normalized_to_title_case(self):
        """full_name se normaliza a title case."""
        req = RegisterRequest(**{**_REGISTER_BASE, "full_name": "juan quispe mamani"})
        assert req.full_name == "Juan Quispe Mamani"

    def test_full_name_strips_whitespace(self):
        """full_name pierde espacios al inicio y final."""
        req = RegisterRequest(**{**_REGISTER_BASE, "full_name": "  Ana Torres  "})
        assert req.full_name == "Ana Torres"

    def test_full_name_min_length(self):
        """full_name de 1 char → ValidationError (mínimo 2)."""
        with pytest.raises(ValidationError):
            RegisterRequest(**{**_REGISTER_BASE, "full_name": "A"})

    def test_full_name_max_length(self):
        """full_name de 151 chars → ValidationError (máximo 150)."""
        with pytest.raises(ValidationError):
            RegisterRequest(**{**_REGISTER_BASE, "full_name": "A" * 151})

    def test_full_name_exactly_2_accepted(self):
        """full_name de 2 chars es aceptado."""
        req = RegisterRequest(**{**_REGISTER_BASE, "full_name": "AB"})
        assert len(req.full_name) == 2

    def test_full_name_exactly_150_accepted(self):
        """full_name de 150 chars es aceptado."""
        req = RegisterRequest(**{**_REGISTER_BASE, "full_name": "A" * 150})
        assert len(req.full_name) == 150

    def test_phone_normalized(self):
        """Teléfono de 9 dígitos se normaliza a +51XXXXXXXXX."""
        req = RegisterRequest(**{**_REGISTER_BASE, "phone_number": "987654321"})
        assert req.phone_number == "+51987654321"

    def test_invalid_phone_raises(self):
        """Teléfono no peruano → ValidationError."""
        with pytest.raises(ValidationError):
            RegisterRequest(**{**_REGISTER_BASE, "phone_number": "+15550000000"})

    def test_password_min_length(self):
        """Contraseña de 5 chars → ValidationError."""
        with pytest.raises(ValidationError):
            RegisterRequest(**{**_REGISTER_BASE, "password": "abc12"})

    def test_password_max_length(self):
        """Contraseña de 129 chars → ValidationError."""
        with pytest.raises(ValidationError):
            RegisterRequest(**{**_REGISTER_BASE, "password": "a" * 129})

    def test_password_6_chars_accepted(self):
        """Contraseña de 6 chars es aceptada."""
        req = RegisterRequest(**{**_REGISTER_BASE, "password": "abcdef"})
        assert req.password == "abcdef"

    def test_email_optional(self):
        """Email es opcional."""
        req = RegisterRequest(**_REGISTER_BASE)
        assert req.email is None

    def test_email_provided(self):
        """Email puede ser proporcionado."""
        req = RegisterRequest(**{**_REGISTER_BASE, "email": "juan@test.com"})
        assert req.email == "juan@test.com"

    def test_missing_full_name_raises(self):
        """full_name faltante → ValidationError."""
        data = {k: v for k, v in _REGISTER_BASE.items() if k != "full_name"}
        with pytest.raises(ValidationError):
            RegisterRequest(**data)

    def test_missing_phone_raises(self):
        """phone_number faltante → ValidationError."""
        data = {k: v for k, v in _REGISTER_BASE.items() if k != "phone_number"}
        with pytest.raises(ValidationError):
            RegisterRequest(**data)

    def test_missing_password_raises(self):
        """password faltante → ValidationError."""
        data = {k: v for k, v in _REGISTER_BASE.items() if k != "password"}
        with pytest.raises(ValidationError):
            RegisterRequest(**data)

    def test_role_defaults_to_passenger(self):
        """Sin role, el valor por defecto es 'passenger'."""
        data = {k: v for k, v in _REGISTER_BASE.items() if k != "role"}
        req = RegisterRequest(**data)
        assert req.role == "passenger"


# =============================================================================
# SendOTPRequest
# =============================================================================


class TestSendOTPRequestSchema:

    def test_valid_phone_verify_purpose(self):
        """purpose='phone_verify' es válido."""
        req = SendOTPRequest(phone_number="+51987654321", purpose="phone_verify")
        assert req.purpose == "phone_verify"

    def test_valid_login_purpose(self):
        """purpose='login' es válido."""
        req = SendOTPRequest(phone_number="+51987654321", purpose="login")
        assert req.purpose == "login"

    def test_valid_password_reset_purpose(self):
        """purpose='password_reset' es válido."""
        req = SendOTPRequest(phone_number="+51987654321", purpose="password_reset")
        assert req.purpose == "password_reset"

    def test_invalid_purpose_raises(self):
        """purpose desconocido → ValidationError."""
        with pytest.raises(ValidationError):
            SendOTPRequest(phone_number="+51987654321", purpose="hack")

    def test_purpose_case_sensitive(self):
        """purpose es sensible a mayúsculas."""
        with pytest.raises(ValidationError):
            SendOTPRequest(phone_number="+51987654321", purpose="Phone_Verify")

    def test_purpose_defaults_to_phone_verify(self):
        """Sin purpose, el valor por defecto es 'phone_verify'."""
        req = SendOTPRequest(phone_number="+51987654321")
        assert req.purpose == "phone_verify"

    def test_phone_normalized(self):
        """Teléfono de 9 dígitos se normaliza."""
        req = SendOTPRequest(phone_number="987654321")
        assert req.phone_number == "+51987654321"

    def test_invalid_phone_raises(self):
        """Teléfono inválido → ValidationError."""
        with pytest.raises(ValidationError):
            SendOTPRequest(phone_number="no-es-telefono")


# =============================================================================
# VerifyOTPRequest
# =============================================================================


class TestVerifyOTPRequestSchema:

    def test_valid_request_parsed(self):
        """Request válido se parsea correctamente."""
        req = VerifyOTPRequest(phone_number="+51987654321", code="123456")
        assert req.code == "123456"

    def test_code_must_be_6_digits(self):
        """Código de exactamente 6 dígitos es aceptado."""
        req = VerifyOTPRequest(phone_number="+51987654321", code="000000")
        assert len(req.code) == 6

    def test_code_5_chars_rejected(self):
        """Código de 5 chars → ValidationError."""
        with pytest.raises(ValidationError):
            VerifyOTPRequest(phone_number="+51987654321", code="12345")

    def test_code_7_chars_rejected(self):
        """Código de 7 chars → ValidationError."""
        with pytest.raises(ValidationError):
            VerifyOTPRequest(phone_number="+51987654321", code="1234567")

    def test_code_with_letters_rejected(self):
        """Código con letras → ValidationError."""
        with pytest.raises(ValidationError):
            VerifyOTPRequest(phone_number="+51987654321", code="12345a")

    def test_code_with_spaces_rejected(self):
        """Código con espacios → ValidationError."""
        with pytest.raises(ValidationError):
            VerifyOTPRequest(phone_number="+51987654321", code="123 56")

    def test_dev_code_123456_accepted(self):
        """El código de desarrollo '123456' es aceptado."""
        req = VerifyOTPRequest(phone_number="+51987654321", code="123456")
        assert req.code == "123456"

    def test_purpose_defaults_to_phone_verify(self):
        """purpose por defecto es 'phone_verify'."""
        req = VerifyOTPRequest(phone_number="+51987654321", code="123456")
        assert req.purpose == "phone_verify"

    def test_missing_code_raises(self):
        """Código faltante → ValidationError."""
        with pytest.raises(ValidationError):
            VerifyOTPRequest(phone_number="+51987654321")


# =============================================================================
# LoginRequest
# =============================================================================


class TestLoginRequestSchema:

    def test_valid_login_parsed(self):
        """Login válido se parsea correctamente."""
        req = LoginRequest(phone_number="+51987654321", password="pass1234")
        assert req.password == "pass1234"

    def test_phone_normalized(self):
        """Teléfono de 9 dígitos se normaliza."""
        req = LoginRequest(phone_number="987654321", password="pass1234")
        assert req.phone_number == "+51987654321"

    def test_invalid_phone_raises(self):
        """Teléfono inválido → ValidationError."""
        with pytest.raises(ValidationError):
            LoginRequest(phone_number="not-phone", password="pass1234")

    def test_device_name_optional(self):
        """device_name es opcional."""
        req = LoginRequest(phone_number="+51987654321", password="pass1234")
        assert req.device_name is None

    def test_device_fields_can_be_provided(self):
        """Los campos de dispositivo se pueden proporcionar."""
        req = LoginRequest(
            phone_number="+51987654321",
            password="pass1234",
            device_name="Pixel 8",
            device_os="Android 14",
        )
        assert req.device_name == "Pixel 8"
        assert req.device_os == "Android 14"

    def test_missing_password_raises(self):
        """Contraseña faltante → ValidationError."""
        with pytest.raises(ValidationError):
            LoginRequest(phone_number="+51987654321")

    def test_missing_phone_raises(self):
        """Teléfono faltante → ValidationError."""
        with pytest.raises(ValidationError):
            LoginRequest(password="pass1234")


# =============================================================================
# UpdateProfileRequest
# =============================================================================


class TestUpdateProfileRequestSchema:

    def test_all_fields_optional(self):
        """Todos los campos son opcionales."""
        req = UpdateProfileRequest()
        assert req.full_name is None
        assert req.email is None
        assert req.preferred_lang is None

    def test_full_name_normalized(self):
        """full_name se normaliza a title case."""
        req = UpdateProfileRequest(full_name="maría torres")
        assert req.full_name == "María Torres"

    def test_full_name_strips_whitespace(self):
        """full_name pierde espacios extra."""
        req = UpdateProfileRequest(full_name="  Luis  ")
        assert req.full_name == "Luis"

    def test_full_name_min_length(self):
        """full_name de 1 char → ValidationError."""
        with pytest.raises(ValidationError):
            UpdateProfileRequest(full_name="A")

    def test_full_name_max_length(self):
        """full_name de 151 chars → ValidationError."""
        with pytest.raises(ValidationError):
            UpdateProfileRequest(full_name="A" * 151)

    def test_full_name_exactly_2_accepted(self):
        """full_name de 2 chars es aceptado."""
        req = UpdateProfileRequest(full_name="AB")
        assert req.full_name is not None

    def test_preferred_lang_max_length(self):
        """preferred_lang de más de 5 chars → ValidationError."""
        with pytest.raises(ValidationError):
            UpdateProfileRequest(preferred_lang="espanol")

    def test_preferred_lang_5_chars_accepted(self):
        """preferred_lang de 5 chars es aceptado."""
        req = UpdateProfileRequest(preferred_lang="es-PE")
        assert req.preferred_lang == "es-PE"

    def test_email_provided(self):
        """Email puede ser proporcionado."""
        req = UpdateProfileRequest(email="nuevo@test.com")
        assert req.email == "nuevo@test.com"

    def test_full_name_none_stays_none(self):
        """full_name=None no falla el validador."""
        req = UpdateProfileRequest(full_name=None)
        assert req.full_name is None


# =============================================================================
# UpdateVehicleRequest
# =============================================================================


class TestUpdateVehicleRequestSchema:

    def test_all_fields_optional(self):
        """Todos los campos son opcionales."""
        req = UpdateVehicleRequest()
        assert req.vehicle_type is None
        assert req.vehicle_year is None
        assert req.vehicle_plate is None

    def test_valid_vehicle_types(self):
        """Los dos tipos de vehículo son aceptados."""
        for vtype in ["mototaxi", "car"]:
            req = UpdateVehicleRequest(vehicle_type=vtype)
            assert req.vehicle_type == vtype

    def test_invalid_vehicle_type_raises(self):
        """Tipo de vehículo inválido → ValidationError."""
        with pytest.raises(ValidationError):
            UpdateVehicleRequest(vehicle_type="bus")

    def test_vehicle_year_min(self):
        """Año anterior a 1990 → ValidationError."""
        with pytest.raises(ValidationError):
            UpdateVehicleRequest(vehicle_year=1989)

    def test_vehicle_year_future_raises(self):
        """Año mayor que el actual → ValidationError."""
        next_year = datetime.now().year + 1
        with pytest.raises(ValidationError):
            UpdateVehicleRequest(vehicle_year=next_year)

    def test_vehicle_year_1990_accepted(self):
        """Año 1990 (mínimo) es aceptado."""
        req = UpdateVehicleRequest(vehicle_year=1990)
        assert req.vehicle_year == 1990

    def test_vehicle_year_current_accepted(self):
        """Año actual es aceptado."""
        current = datetime.now().year
        req = UpdateVehicleRequest(vehicle_year=current)
        assert req.vehicle_year == current

    def test_vehicle_plate_normalized_to_uppercase(self):
        """Placa se normaliza a mayúsculas."""
        req = UpdateVehicleRequest(vehicle_plate="t3g-847")
        assert req.vehicle_plate == "T3G-847"

    def test_vehicle_plate_strips_whitespace(self):
        """Placa pierde espacios."""
        req = UpdateVehicleRequest(vehicle_plate="  ABC123  ")
        assert req.vehicle_plate == "ABC123"

    def test_vehicle_seats_min(self):
        """Asientos = 0 → ValidationError."""
        with pytest.raises(ValidationError):
            UpdateVehicleRequest(vehicle_seats=0)

    def test_vehicle_seats_max(self):
        """Asientos = 7 → ValidationError."""
        with pytest.raises(ValidationError):
            UpdateVehicleRequest(vehicle_seats=7)

    def test_vehicle_seats_1_accepted(self):
        """1 asiento (mínimo) es aceptado."""
        req = UpdateVehicleRequest(vehicle_seats=1)
        assert req.vehicle_seats == 1

    def test_vehicle_seats_6_accepted(self):
        """6 asientos (máximo) es aceptado."""
        req = UpdateVehicleRequest(vehicle_seats=6)
        assert req.vehicle_seats == 6

    def test_vehicle_brand_max_length(self):
        """Marca de más de 100 chars → ValidationError."""
        with pytest.raises(ValidationError):
            UpdateVehicleRequest(vehicle_brand="B" * 101)

    def test_vehicle_model_max_length(self):
        """Modelo de más de 100 chars → ValidationError."""
        with pytest.raises(ValidationError):
            UpdateVehicleRequest(vehicle_model="M" * 101)

    def test_vehicle_color_max_length(self):
        """Color de más de 50 chars → ValidationError."""
        with pytest.raises(ValidationError):
            UpdateVehicleRequest(vehicle_color="C" * 51)

    def test_vehicle_type_none_stays_none(self):
        """vehicle_type=None no falla el validador."""
        req = UpdateVehicleRequest(vehicle_type=None)
        assert req.vehicle_type is None
