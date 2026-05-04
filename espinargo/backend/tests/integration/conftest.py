"""
Fixtures compartidas para tests de integración.

Provee cliente HTTP, DB de test y usuarios pre-creados
(pasajero verificado y conductor aprobado).

Todos los fixtures de usuario son session-scoped para evitar problemas
de event loop con el singleton de Redis en pytest-asyncio.
"""

import pytest_asyncio
import redis.asyncio as aioredis
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.user import DriverProfile, DriverStatus, User, UserRole, UserStatus

test_db_url = settings.DATABASE_URL.replace("espinargo_db", "espinargo_test")
test_engine = create_async_engine(test_db_url, poolclass=NullPool)
TestSession = async_sessionmaker(test_engine, expire_on_commit=False)


async def override_get_db():
    async with TestSession() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    # Limpiar Redis para evitar rate limits de ejecuciones anteriores
    redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    await redis.flushdb()
    await redis.aclose()

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="session")
async def client():
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="session")
async def passenger_token() -> str:
    """Crea un usuario pasajero directamente en la DB y retorna su token."""
    async with TestSession() as db:
        result = await db.execute(
            select(User).where(User.phone_number == "+51900000001")
        )
        passenger = result.scalar_one_or_none()

        if not passenger:
            passenger = User(
                full_name="Pasajero Test",
                phone_number="+51900000001",
                email="pasajero@test.com",
                password_hash=hash_password("pass1234"),
                role=UserRole.PASSENGER,
                status=UserStatus.ACTIVE,
                phone_verified=True,
            )
            db.add(passenger)
            await db.commit()
            await db.refresh(passenger)

    return create_access_token(
        user_id=passenger.id,
        role="passenger",
        phone_number=passenger.phone_number,
    )


@pytest_asyncio.fixture(scope="session")
async def driver_token() -> str:
    """Crea un conductor aprobado directamente en la DB y retorna su token."""
    async with TestSession() as db:
        result = await db.execute(
            select(User).where(User.phone_number == "+51900000002")
        )
        driver = result.scalar_one_or_none()

        if not driver:
            driver = User(
                full_name="Conductor Test",
                phone_number="+51900000002",
                email="conductor@test.com",
                password_hash=hash_password("pass1234"),
                role=UserRole.DRIVER,
                status=UserStatus.ACTIVE,
                phone_verified=True,
            )
            db.add(driver)
            await db.flush()

            dp = DriverProfile(
                user_id=driver.id,
                driver_status=DriverStatus.APPROVED,
            )
            db.add(dp)
            await db.commit()
            await db.refresh(driver)
        else:
            # Asegurar que el conductor esté aprobado
            result_dp = await db.execute(
                select(DriverProfile).where(DriverProfile.user_id == driver.id)
            )
            dp = result_dp.scalar_one_or_none()
            if dp:
                dp.driver_status = DriverStatus.APPROVED
                await db.commit()

    return create_access_token(
        user_id=driver.id,
        role="driver",
        phone_number=driver.phone_number,
    )


@pytest_asyncio.fixture(scope="session")
async def admin_token() -> str:
    """Crea un usuario admin directamente en la DB y retorna su token."""
    async with TestSession() as db:
        result = await db.execute(
            select(User).where(User.phone_number == "+51900000003")
        )
        admin = result.scalar_one_or_none()

        if not admin:
            admin = User(
                full_name="Admin Test",
                phone_number="+51900000003",
                email="admin@test.com",
                password_hash=hash_password("adminpass"),
                role=UserRole.ADMIN,
                status=UserStatus.ACTIVE,
                phone_verified=True,
            )
            db.add(admin)
            await db.commit()
            await db.refresh(admin)

    return create_access_token(
        user_id=admin.id,
        role="admin",
        phone_number=admin.phone_number,
    )
