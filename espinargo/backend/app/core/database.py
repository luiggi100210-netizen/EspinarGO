"""
Módulo de conexión a la base de datos PostgreSQL.

Maneja toda la conexión con PostgreSQL de forma asíncrona usando
SQLAlchemy 2.0 con async/await. Provee el motor de base de datos,
la fábrica de sesiones y una dependencia de FastAPI lista para usar.

Uso en endpoints:
    from fastapi import Depends
    from app.core.database import get_db

    @app.get("/users")
    async def get_users(db: AsyncSession = Depends(get_db)):
        result = await db.execute(select(User))
        return result.scalars().all()
"""

from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


# =============================================================================
# ENGINE - Motor de base de datos async
# =============================================================================

# Crear el engine async con la URL de la configuración
# - echo: muestra las queries en consola solo en modo DEBUG
# - pool_size: 20 conexiones simultáneas en el pool
# - max_overflow: 40 conexiones adicionales bajo alta carga
# - pool_pre_ping: verifica la conexión antes de usarla (evita errores de conexión perdida)
# - pool_recycle: recicla conexiones cada hora (evita timeouts de PostgreSQL)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=3600,
)


# =============================================================================
# SESSION FACTORY - Fábrica de sesiones async
# =============================================================================

# Crear el sessionmaker para generar sesiones async
# - expire_on_commit=False: los objetos no expiran tras el commit,
#   permitiendo acceder a las relaciones después de cerrar la sesión
# - autocommit=False: requiere commit explícito para guardar cambios
# - autoflush=False: requiere flush explícito para sincronizar con la DB
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# =============================================================================
# BASE - Clase base para todos los modelos ORM
# =============================================================================

class Base(DeclarativeBase):
    """
    Clase base para todos los modelos de la aplicación.

    Todos los modelos (User, Trip, Package, etc.) deben heredar de esta Base.
    Esto permite que SQLAlchemy los registre automáticamente para las migraciones.
    """

    pass


# =============================================================================
# DEPENDENCY - Función para usar en endpoints de FastAPI
# =============================================================================

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependencia de FastAPI para obtener una sesión de base de datos.

    Esta función se usa con Depends() en los endpoints. Abre una sesión,
    la entrega al endpoint, y la cierra automáticamente.

    Comportamiento:
    - Si el endpoint termina sin errores: hace commit automáticamente
    - Si hay error: hace rollback automáticamente
    - Siempre cierra la sesión al final (bloque finally)

    Args:
        Ninguno (toma la sesión del sessionmaker)

    Yields:
        AsyncSession: Sesión de base de datos para usar en el endpoint

    Ejemplo de uso en un endpoint:
        from fastapi import APIRouter, Depends
        from sqlalchemy.ext.asyncio import AsyncSession

        router = APIRouter()

        @router.get("/users")
        async def list_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(text("SELECT * FROM users"))
            return result.fetchall()

    Returns:
        AsyncGenerator que produce una AsyncSession
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# =============================================================================
# HEALTH CHECK - Función para verificar conexión a la DB
# =============================================================================

async def check_database_connection() -> bool:
    """
    Verifica si la conexión a la base de datos está activa.

    Ejecuta una query simple "SELECT 1" para verificar la conectividad.
    Útil para endpoints de health check y monitoreo.

    Returns:
        bool: True si la conexión está activa, False si hay error

    Ejemplo de uso:
        from app.core.database import check_database_connection

        is_connected = await check_database_connection()
        print(f"DB conectada: {is_connected}")
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False