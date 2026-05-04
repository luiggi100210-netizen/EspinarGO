"""
Fixtures compartidas para tests de integración.

Provee cliente HTTP, DB de test y usuarios pre-creados
(pasajero verificado y conductor aprobado).
"""

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app
from app.models.user import DriverProfile, DriverStatus, User, UserRole, UserStatus
from app.core.security import hash_password

test_db_url = settings.DATABASE_URL.replace("espinargo_db", "espinargo_test")
test_engine = create_async_engine(test_db_url, poolclass=NullPool)
TestSession = async_sessionmaker(test_engine, expire_on_commit=False)


async def override_get_db():
    async with TestSession() as session:
        yield session


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def passenger_token(client: AsyncClient) -> str:
    await client.post("/api/v1/auth/register", json={
        "full_name": "Pasajero Test",
        "phone_number": "+51900000001",
        "email": "pasajero@test.com",
        "password": "pass1234",
        "role": "passenger",
    })
    await client.post("/api/v1/auth/verify-phone", json={
        "phone_number": "+51900000001",
        "code": "123456",
        "purpose": "phone_verify",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "phone_number": "+51900000001",
        "password": "pass1234",
    })
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def driver_token(client: AsyncClient) -> str:
    await client.post("/api/v1/auth/register", json={
        "full_name": "Conductor Test",
        "phone_number": "+51900000002",
        "email": "conductor@test.com",
        "password": "pass1234",
        "role": "driver",
    })
    await client.post("/api/v1/auth/verify-phone", json={
        "phone_number": "+51900000002",
        "code": "123456",
        "purpose": "phone_verify",
    })

    async with TestSession() as db:
        from sqlalchemy import select
        result = await db.execute(
            select(User).where(User.phone_number == "+51900000002")
        )
        user = result.scalar_one()
        dp = user.driver_profile
        dp.driver_status = DriverStatus.APPROVED
        await db.commit()

    resp = await client.post("/api/v1/auth/login", json={
        "phone_number": "+51900000002",
        "password": "pass1234",
    })
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient) -> str:
    """Crea un usuario admin directamente en la DB y retorna su token."""
    from sqlalchemy import select
    from app.core.security import create_access_token

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
                hashed_password=hash_password("adminpass"),
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
