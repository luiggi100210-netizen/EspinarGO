"""
Script para crear el usuario administrador inicial.

Se ejecuta después de init_db.py.
Tiene protección para no crear duplicados.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import select

from app.core.config import settings
from app.core.security import hash_password
from app.models.user import User, UserRole, UserStatus


async def create_admin() -> None:
    """Crea el usuario administrador si no existe."""
    engine = create_async_engine(settings.DATABASE_URL)
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as db:
        result = await db.execute(
            select(User).where(User.phone_number == "+51900000001")
        )
        existing_admin = result.scalar_one_or_none()

        if existing_admin:
            print("\n⚠️  Ya existe un admin con este número.")
            print("    Teléfono: +51900000001")
            await engine.dispose()
            return

        admin = User(
            full_name="Administrador EspinarGo",
            phone_number="+51900000001",
            email="admin@espinargo.com",
            password_hash=hash_password("Admin@EspinarGo2024!"),
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            phone_verified=True,
            email_verified=True,
        )

        db.add(admin)
        await db.commit()

        await engine.dispose()

        print("\n" + "=" * 50)
        print("  ✅ ADMIN CREADO EXITOSAMENTE")
        print("=" * 50)
        print("\n📋 Credenciales de acceso:")
        print(f"   Teléfono: +51900000001")
        print(f"   Contraseña: Admin@EspinarGo2024!")
        print("\n⚠️  IMPORTANTE:")
        print("   Cambia esta contraseña inmediatamente en producción.")
        print("   Ve a: POST /api/v1/auth/change-password")
        print("=" * 50)


async def main() -> None:
    """Función principal del script."""
    print("\n" + "=" * 50)
    print("  ESPINARGO - Crear Usuario Administrador")
    print("=" * 50 + "\n")

    await create_admin()

    print("\n📌 Para iniciar la aplicación:")
    print("   uvicorn app.main:app --reload --port 8000")
    print("\n📚 Documentación:")
    print("   http://localhost:8000/docs\n")


if __name__ == "__main__":
    asyncio.run(main())