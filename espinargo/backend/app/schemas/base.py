"""
Validadores y configuraciones reutilizables para todos los schemas.

Este archivo centraliza la lógica de validación común para evitar
código duplicado en los schemas. Todos los schemas heredan de
EspinarGoBaseModel que incluye esta configuración base.
"""

import re
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EspinarGoBaseModel(BaseModel):
    """
    Clase base para todos los schemas de la aplicación.

    Configuración:
    - from_attributes=True: permite crear schemas desde modelos
      SQLAlchemy directamente con model_validate()
    - populate_by_name=True: acepta tanto alias como nombre original
    - str_strip_whitespace=True: elimina espacios al inicio y fin
      automáticamente
    - use_enum_values=True: usa el valor del enum, no el objeto
    """

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        use_enum_values=True,
    )


def validate_peru_phone(phone: str) -> str:
    """
    Valida y normaliza números de celular peruanos.

    El formato esperado es +519XXXXXXXXX donde X son 9 dígitos.

    Proceso de normalización:
    1. Eliminar espacios, guiones y paréntesis
    2. Convertir al formato +51 si es necesario
    3. Validar contra el regex de celulares válidos

    Args:
        phone: Número de teléfono en cualquier formato.

    Returns:
        str: Número normalizado en formato +51XXXXXXXXX.

    Raises:
        ValueError: Si el número no es válido.

    Examples:
        >>> validate_peru_phone("+51987654321")
        '+51987654321'
        >>> validate_peru_phone("987654321")
        '+51987654321'
        >>> validate_peru_phone("51987654321")
        '+51987654321'
        >>> validate_peru_phone("123456")
        ValueError(...)
    """
    cleaned = re.sub(r"[\s\-\(\)]", "", phone)

    if cleaned.startswith("51") and len(cleaned) == 11:
        cleaned = "+" + cleaned
    elif cleaned.startswith("9") and len(cleaned) == 9:
        cleaned = "+51" + cleaned

    regex = r"^\+51[9][0-9]{8}$"
    if not re.match(regex, cleaned):
        raise ValueError(
            "Número inválido. Debe ser un celular peruano que "
            "empiece con 9. Ejemplo: +51987654321"
        )

    return cleaned


def validate_password_strength(password: str) -> str:
    """
    Valida que la contraseña cumple requisitos mínimos.

    Requisitos:
    - Mínimo 6 caracteres (balance entre seguridad y usabilidad
      para usuarios en Espinar que pueden no estar familiarizados
      con contraseñas complejas)
    - Máximo 128 caracteres

    Args:
        password: Contraseña en texto plano.

    Returns:
        str: La contraseña tal como viene.

    Raises:
        ValueError: Si no cumple los requisitos.

    Examples:
        >>> validate_password_strength("mi123")
        ValueError(...)
        >>> validate_password_strength("miClave123")
        'miClave123'
    """
    if len(password) < 6:
        raise ValueError("La contraseña debe tener mínimo 6 caracteres")
    if len(password) > 128:
        raise ValueError("La contraseña es demasiado larga (máx 128)")
    return password


def validate_price(price: str) -> str:
    """
    Valida precios en soles para viajes y encomiendas.

    El precio se guarda como string para evitar problemas de
    precisión con números de punto flotante en dinero.

    Args:
        price: Precio como string.

    Returns:
        str: Precio formateado con 2 decimales.

    Raises:
        ValueError: Si el precio es inválido o fuera de rango.

    Examples:
        >>> validate_price("5")
        '5.00'
        >>> validate_price("5.5")
        '5.50'
        >>> validate_price("0")
        ValueError(...)
    """
    try:
        value = float(price)
    except (ValueError, TypeError):
        raise ValueError("El precio debe ser un número. Ejemplo: 5.50")

    if value <= 0:
        raise ValueError("El precio debe ser mayor a cero")

    if value > 999:
        raise ValueError("El precio máximo es S/999")

    return f"{value:.2f}"


def validate_score(score: int) -> int:
    """
    Valida calificaciones de 1 a 5 estrellas.

    Args:
        score: Número de estrellas.

    Returns:
        int: El score validado.

    Raises:
        ValueError: Si el score está fuera de rango.

    Examples:
        >>> validate_score(3)
        3
        >>> validate_score(0)
        ValueError(...)
    """
    if score < 1 or score > 5:
        raise ValueError("La calificación debe ser entre 1 y 5 estrellas")
    return score


class MessageResponse(EspinarGoBaseModel):
    """
    Respuesta genérica para operaciones exitosas.
    """

    message: str = Field(..., description="Mensaje descriptivo de la operación")
    success: bool = Field(default=True, description="Indica si la operación fue exitosa")


class ErrorResponse(EspinarGoBaseModel):
    """
    Formato estándar de errores de la API.
    """

    detail: str = Field(..., description="Descripción del error en español")
    code: Optional[str] = Field(default=None, description="Código de error interno")


class PaginationMeta(EspinarGoBaseModel):
    """
    Metadata de paginación para listas largas.
    """

    total: int = Field(..., description="Total de registros en la base de datos")
    page: int = Field(..., description="Página actual (empieza en 1)")
    per_page: int = Field(..., description="Registros por página")
    total_pages: int = Field(..., description="Total de páginas calculado")
    has_next: bool = Field(..., description="True si hay página siguiente")
    has_prev: bool = Field(..., description="True si hay página anterior")

    @classmethod
    def create(
        cls,
        total: int,
        page: int,
        per_page: int,
    ) -> "PaginationMeta":
        """
        Factory method para crear la metadata de paginación.

        Args:
            total: Total de registros.
            page: Página actual.
            per_page: Registros por página.

        Returns:
            PaginationMeta: Metadata calculada.
        """
        total_pages = (total + per_page - 1) // per_page
        return cls(
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )