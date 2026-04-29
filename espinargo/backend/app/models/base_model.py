"""
Módulo de modelos base con campos comunes reutilizables.

Define mixins que centralizan campos que comparten todos los modelos:
- id: UUID como clave primaria (no secuencial)
- created_at: fecha de creación automática
- updated_at: fecha de última modificación automática

El uso de UUID en lugar de Integer autoincremental tiene beneficios:
- Mayor seguridad (no revela la cantidad de registros)
- Escalabilidad (funciona en sistemas distribuidos)
- Merge de bases de datos sin conflictos de IDs
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """
    Mixin que añade campos de tiempo a cualquier modelo.

    Define created_at y updated_at que se gestionan automáticamente
    por la base de datos (server_default y onupdate).
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="fecha y hora exacta de creación del registro",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="se actualiza cada vez que el registro cambia",
    )


class UUIDMixin:
    """
    Mixin que añade un ID UUID como clave primaria.

    El UUID es un identificador único de 128 bits que no es secuencial,
    a diferencia de los Integer autoincrementales. Esto es preferible
    para:
    - Evitar que usuarios adivinen IDs de otros registros
    - Permitir merge de bases de datos sin conflictos
    - Funcionar bien en sistemas distribuidos
    """

    id: Mapped[uuid4] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
        doc="identificador único universal, no secuencial para mayor seguridad y escalabilidad",
    )


class BaseModel(UUIDMixin, TimestampMixin):
    """
    Clase base que combina UUID y Timestamp.

    Todos los modelos de la aplicación heredan de esta clase
    para obtener automáticamente los campos:
    - id: UUID único como primary key
    - created_at: fecha de creación
    - updated_at: fecha de última modificación
    """

    pass