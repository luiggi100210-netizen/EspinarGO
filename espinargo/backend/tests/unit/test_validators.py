"""
Tests unitarios para los validadores reutilizables de base.py.

Cubre: validate_peru_phone, validate_price, validate_password_strength,
validate_score y PaginationMeta.create — todos son funciones puras sin DB.
"""

import pytest

from app.schemas.base import (
    PaginationMeta,
    validate_password_strength,
    validate_peru_phone,
    validate_price,
    validate_score,
)


# =============================================================================
# validate_peru_phone
# =============================================================================


class TestValidatePeruPhone:

    def test_standard_format_accepted(self):
        """Formato canónico +51XXXXXXXXX es aceptado sin cambios."""
        assert validate_peru_phone("+51987654321") == "+51987654321"

    def test_nine_digit_normalized(self):
        """Número de 9 dígitos sin prefijo se normaliza a +51XXXXXXXXX."""
        assert validate_peru_phone("987654321") == "+51987654321"

    def test_prefix_51_without_plus_normalized(self):
        """Número con '51' sin '+' se normaliza a +51XXXXXXXXX."""
        assert validate_peru_phone("51987654321") == "+51987654321"

    def test_spaces_and_dashes_stripped(self):
        """Espacios y guiones se eliminan antes de validar."""
        assert validate_peru_phone("+51 987-654-321") == "+51987654321"

    def test_parentheses_stripped(self):
        """Paréntesis se eliminan antes de validar."""
        assert validate_peru_phone("+51(987)654321") == "+51987654321"

    def test_non_peruvian_number_rejected(self):
        """Número de EE.UU. → ValueError."""
        with pytest.raises(ValueError, match="celular peruano"):
            validate_peru_phone("+15550000000")

    def test_short_number_rejected(self):
        """Número demasiado corto → ValueError."""
        with pytest.raises(ValueError):
            validate_peru_phone("123")

    def test_landline_prefix_rejected(self):
        """Celular peruano debe empezar con 9 (no 6 o 7) → ValueError."""
        with pytest.raises(ValueError):
            validate_peru_phone("+51612345678")

    def test_too_long_rejected(self):
        """Número con dígitos de más → ValueError."""
        with pytest.raises(ValueError):
            validate_peru_phone("+519876543210")  # 10 dígitos tras 51

    def test_empty_string_rejected(self):
        """Cadena vacía → ValueError."""
        with pytest.raises(ValueError):
            validate_peru_phone("")

    def test_letters_only_rejected(self):
        """Solo letras → ValueError."""
        with pytest.raises(ValueError):
            validate_peru_phone("telefono")

    def test_returns_string(self):
        """El resultado siempre es un str."""
        result = validate_peru_phone("+51900000001")
        assert isinstance(result, str)

    def test_number_starting_with_9_various(self):
        """Distintos números válidos con prefijo 9."""
        for num in ["900000001", "912345678", "999999999"]:
            result = validate_peru_phone(num)
            assert result.startswith("+51")
            assert len(result) == 12


# =============================================================================
# validate_price
# =============================================================================


class TestValidatePrice:

    def test_integer_string_formatted(self):
        """'5' → '5.00'."""
        assert validate_price("5") == "5.00"

    def test_single_decimal_formatted(self):
        """'5.5' → '5.50'."""
        assert validate_price("5.5") == "5.50"

    def test_two_decimals_kept(self):
        """'5.50' → '5.50'."""
        assert validate_price("5.50") == "5.50"

    def test_max_valid_price(self):
        """'999' → '999.00' (precio máximo permitido)."""
        assert validate_price("999") == "999.00"

    def test_min_valid_price(self):
        """'0.01' → '0.01' (precio mínimo > 0)."""
        assert validate_price("0.01") == "0.01"

    def test_zero_rejected(self):
        """'0' → ValueError (precio debe ser > 0)."""
        with pytest.raises(ValueError, match="mayor a cero"):
            validate_price("0")

    def test_negative_rejected(self):
        """-1 → ValueError."""
        with pytest.raises(ValueError, match="mayor a cero"):
            validate_price("-1")

    def test_above_max_rejected(self):
        """'1000' → ValueError (máximo S/999)."""
        with pytest.raises(ValueError, match="999"):
            validate_price("1000")

    def test_non_numeric_rejected(self):
        """Cadena no numérica → ValueError."""
        with pytest.raises(ValueError, match="número"):
            validate_price("diez soles")

    def test_empty_string_rejected(self):
        """Cadena vacía → ValueError."""
        with pytest.raises(ValueError):
            validate_price("")

    def test_returns_string(self):
        """El resultado siempre es un str."""
        assert isinstance(validate_price("8"), str)

    def test_large_valid_price(self):
        """'500.75' → '500.75'."""
        assert validate_price("500.75") == "500.75"


# =============================================================================
# validate_password_strength
# =============================================================================


class TestValidatePasswordStrength:

    def test_minimum_length_accepted(self):
        """Contraseña de exactamente 6 chars es aceptada."""
        assert validate_password_strength("abcdef") == "abcdef"

    def test_normal_password_accepted(self):
        """Contraseña típica es aceptada."""
        assert validate_password_strength("miClave123") == "miClave123"

    def test_max_length_accepted(self):
        """Contraseña de 128 chars (máximo) es aceptada."""
        pw = "a" * 128
        assert validate_password_strength(pw) == pw

    def test_too_short_rejected(self):
        """Contraseña de 5 chars → ValueError."""
        with pytest.raises(ValueError, match="mínimo 6"):
            validate_password_strength("abc12")

    def test_empty_rejected(self):
        """Contraseña vacía → ValueError."""
        with pytest.raises(ValueError, match="mínimo 6"):
            validate_password_strength("")

    def test_too_long_rejected(self):
        """Contraseña de 129 chars → ValueError."""
        with pytest.raises(ValueError, match="128"):
            validate_password_strength("a" * 129)

    def test_exactly_5_chars_rejected(self):
        """5 caracteres exactos → ValueError."""
        with pytest.raises(ValueError):
            validate_password_strength("12345")

    def test_exactly_6_chars_accepted(self):
        """6 caracteres exactos → aceptada."""
        result = validate_password_strength("123456")
        assert result == "123456"

    def test_returns_unchanged_password(self):
        """La función retorna la contraseña sin modificar."""
        pw = "Test1234!"
        assert validate_password_strength(pw) == pw

    def test_unicode_password_accepted(self):
        """Contraseñas con caracteres Unicode son aceptadas."""
        pw = "clave123ñ"
        assert validate_password_strength(pw) == pw

    def test_special_chars_accepted(self):
        """Caracteres especiales son permitidos."""
        pw = "!@#$%^"
        assert validate_password_strength(pw) == pw


# =============================================================================
# validate_score
# =============================================================================


class TestValidateScore:

    def test_score_1_accepted(self):
        """Score 1 (mínimo) es válido."""
        assert validate_score(1) == 1

    def test_score_5_accepted(self):
        """Score 5 (máximo) es válido."""
        assert validate_score(5) == 5

    def test_score_3_accepted(self):
        """Score 3 (medio) es válido."""
        assert validate_score(3) == 3

    def test_score_0_rejected(self):
        """Score 0 → ValueError."""
        with pytest.raises(ValueError, match="1 y 5"):
            validate_score(0)

    def test_score_6_rejected(self):
        """Score 6 → ValueError."""
        with pytest.raises(ValueError, match="1 y 5"):
            validate_score(6)

    def test_score_negative_rejected(self):
        """Score negativo → ValueError."""
        with pytest.raises(ValueError):
            validate_score(-1)

    def test_score_100_rejected(self):
        """Score muy alto → ValueError."""
        with pytest.raises(ValueError):
            validate_score(100)

    def test_returns_int(self):
        """El resultado es un int."""
        assert isinstance(validate_score(4), int)

    def test_all_valid_scores(self):
        """Todos los scores del 1 al 5 son aceptados."""
        for s in range(1, 6):
            assert validate_score(s) == s


# =============================================================================
# PaginationMeta.create
# =============================================================================


class TestPaginationMeta:

    def test_first_page_has_no_prev(self):
        """Página 1 nunca tiene página anterior."""
        meta = PaginationMeta.create(total=10, page=1, per_page=5)
        assert meta.has_prev is False

    def test_first_page_has_next_when_more_pages(self):
        """Página 1 tiene siguiente si hay más páginas."""
        meta = PaginationMeta.create(total=10, page=1, per_page=5)
        assert meta.has_next is True

    def test_last_page_has_no_next(self):
        """Última página no tiene siguiente."""
        meta = PaginationMeta.create(total=10, page=2, per_page=5)
        assert meta.has_next is False

    def test_last_page_has_prev(self):
        """Última página tiene página anterior."""
        meta = PaginationMeta.create(total=10, page=2, per_page=5)
        assert meta.has_prev is True

    def test_total_pages_calculation(self):
        """total_pages se calcula correctamente."""
        meta = PaginationMeta.create(total=10, page=1, per_page=3)
        assert meta.total_pages == 4  # ceil(10/3)

    def test_exact_division_total_pages(self):
        """División exacta: 10/5 = 2 páginas."""
        meta = PaginationMeta.create(total=10, page=1, per_page=5)
        assert meta.total_pages == 2

    def test_empty_result_zero_pages(self):
        """Sin resultados: total=0 → total_pages=0, no next, no prev."""
        meta = PaginationMeta.create(total=0, page=1, per_page=20)
        assert meta.total_pages == 0
        assert meta.has_next is False
        assert meta.has_prev is False

    def test_single_result_one_page(self):
        """Un solo resultado: total=1, per_page=20 → 1 página."""
        meta = PaginationMeta.create(total=1, page=1, per_page=20)
        assert meta.total_pages == 1
        assert meta.has_next is False

    def test_meta_fields_match_inputs(self):
        """Los campos total, page, per_page reflejan los inputs."""
        meta = PaginationMeta.create(total=50, page=3, per_page=10)
        assert meta.total == 50
        assert meta.page == 3
        assert meta.per_page == 10

    def test_middle_page_has_next_and_prev(self):
        """Página intermedia tiene tanto siguiente como anterior."""
        meta = PaginationMeta.create(total=30, page=2, per_page=10)
        assert meta.has_next is True
        assert meta.has_prev is True

    def test_per_page_one_many_pages(self):
        """per_page=1 con total=5 genera 5 páginas."""
        meta = PaginationMeta.create(total=5, page=1, per_page=1)
        assert meta.total_pages == 5
        assert meta.has_next is True

    def test_total_less_than_per_page_one_page(self):
        """total < per_page → siempre 1 página."""
        meta = PaginationMeta.create(total=3, page=1, per_page=20)
        assert meta.total_pages == 1
        assert meta.has_next is False
