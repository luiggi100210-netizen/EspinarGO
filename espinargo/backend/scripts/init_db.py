"""
Script para inicializar la base de datos.

Crea todas las tablas necesarias para EspinarGo.
Se ejecuta una sola vez al desplegar por primera vez.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.core.database import Base

# Importar modelos en orden para respetar relaciones FK
from app.models.user import User, RefreshToken, OTPCode, DriverProfile
from app.models.trip import Trip, TripOffer
from app.models.package import Package, PackageTracking
from app.models.rating import Rating


async def create_tables() -> None:
    """Crea todas las tablas en la base de datos."""
    print("\n📦 Creando tablas en la base de datos...")

    engine = create_async_engine(settings.DATABASE_URL, echo=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await engine.dispose()

    print("\n✅ Tablas creadas correctamente:")
    print("   - users")
    print("   - refresh_tokens")
    print("   - otp_codes")
    print("   - driver_profiles")
    print("   - trips")
    print("   - trip_offers")
    print("   - packages")
    print("   - package_tracking")
    print("   - ratings")


async def main() -> None:
    """Función principal del script."""
    print("\n" + "=" * 50)
    print("  ESPINARGO - Inicializar Base de Datos")
    print("=" * 50)

    await create_tables()

    print("\n" + "-" * 50)
    print("📌 Próximo paso:")
    print("   python scripts/create_admin.py")
    print("-" * 50)

    print(f"\n📚 Documentación: http://localhost:8000/docs\n")


if __name__ == "__main__":
    asyncio.run(main())