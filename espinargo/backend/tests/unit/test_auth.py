"""
Tests unitarios del módulo de autenticación.

Prueba los endpoints más críticos: registro, verificación OTP,
login, perfil y refresh token.
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

import app.services.otp_service as otp_module
from app.main import app
from app.core.config import settings
from app.core.database import Base, get_db


TEST_PASSENGER = {
    "full_name": "Juan Quispe Mamani",
    "phone_number": "+51987654321",
    "email": "juan@test.com",
    "password": "miClave123",
    "role": "passenger",
}

TEST_DRIVER = {
    "full_name": "Carlos Díaz López",
    "phone_number": "+51976543210",
    "email": "carlos@test.com",
    "password": "driverPass456",
    "role": "driver",
}


test_db_url = settings.DATABASE_URL.replace("espinargo_db", "espinargo_test")
test_engine = create_async_engine(test_db_url, poolclass=NullPool)
TestAsyncSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


async def override_get_db():
    async with TestAsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
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


@pytest_asyncio.fixture(autouse=True)
async def clean_between_tests():
    """Limpia la BD y Redis antes y después de cada test.

    Setup:
      - Resetea el singleton de Redis (evita 'Future attached to a different loop').
      - Crea una conexión temporal para borrar claves de rate-limit acumuladas
        de runs anteriores o del test previo.

    Teardown:
      - Trunca todas las tablas para dejar la BD limpia.
      - Cierra y resetea el cliente Redis del test actual.
    """
    # 1. Flush Redis para eliminar claves de rate-limit acumuladas
    otp_module._redis_client = None
    _tmp = await otp_module.get_redis()
    await _tmp.flushdb()
    await _tmp.aclose()
    otp_module._redis_client = None  # el test crea su propia conexión cuando la necesite

    yield

    # 2. Limpiar BD
    async with TestAsyncSessionLocal() as session:
        await session.execute(text(
            "TRUNCATE TABLE ratings, trip_offers, trips, "
            "package_tracking, packages, otp_codes, refresh_tokens, "
            "driver_profiles, users RESTART IDENTITY CASCADE"
        ))
        await session.commit()

    # 3. Cerrar y resetear el cliente Redis creado durante el test
    if otp_module._redis_client is not None:
        await otp_module._redis_client.aclose()
    otp_module._redis_client = None


async def register_and_verify(client: AsyncClient, data: dict) -> dict:
    """Helper para registrar y verificar un usuario."""
    reg_response = await client.post("/api/v1/auth/register", json=data)
    assert reg_response.status_code == 201

    verify_response = await client.post(
        "/api/v1/auth/verify-phone",
        json={"phone_number": data["phone_number"], "code": "123456", "purpose": "phone_verify"},
    )
    assert verify_response.status_code == 200

    return reg_response.json()


class TestRegister:
    """Tests para el endpoint de registro."""

    @pytest.mark.asyncio
    async def test_register_passenger_success(self, client: AsyncClient):
        """Verifica que un pasajero puede registrarse correctamente."""
        response = await client.post("/api/v1/auth/register", json=TEST_PASSENGER)

        assert response.status_code == 201
        data = response.json()
        assert "user_id" in data
        assert data["next_step"] == "verify_phone"

    @pytest.mark.asyncio
    async def test_register_driver_creates_profile(self, client: AsyncClient):
        """Verifica que registrar un conductor crea su perfil."""
        response = await client.post("/api/v1/auth/register", json=TEST_DRIVER)

        assert response.status_code == 201
        data = response.json()
        assert "user_id" in data

    @pytest.mark.asyncio
    async def test_register_duplicate_phone(self, client: AsyncClient):
        """Verifica que no se puede registrar dos veces el mismo teléfono."""
        await client.post("/api/v1/auth/register", json=TEST_PASSENGER)

        response = await client.post("/api/v1/auth/register", json=TEST_PASSENGER)

        assert response.status_code == 400
        assert "ya está registrado" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_invalid_phone(self, client: AsyncClient):
        """Verifica que un número inválido es rechazado."""
        invalid_data = {**TEST_PASSENGER, "phone_number": "123456"}
        response = await client.post("/api/v1/auth/register", json=invalid_data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_short_password(self, client: AsyncClient):
        """Verifica que una contraseña muy corta es rechazada."""
        invalid_data = {**TEST_PASSENGER, "password": "123"}
        response = await client.post("/api/v1/auth/register", json=invalid_data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_invalid_role(self, client: AsyncClient):
        """Verifica que un rol inválido es rechazado."""
        invalid_data = {**TEST_PASSENGER, "role": "superadmin"}
        response = await client.post("/api/v1/auth/register", json=invalid_data)

        assert response.status_code == 422


class TestOTP:
    """Tests para verificación OTP."""

    @pytest.mark.asyncio
    async def test_verify_phone_dev_code(self, client: AsyncClient):
        """Verifica que en desarrollo el código siempre es 123456."""
        await client.post("/api/v1/auth/register", json=TEST_PASSENGER)

        response = await client.post(
            "/api/v1/auth/verify-phone",
            json={"phone_number": TEST_PASSENGER["phone_number"], "code": "123456"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["verified"] is True

    @pytest.mark.asyncio
    async def test_verify_wrong_code(self, client: AsyncClient):
        """Verifica que un código incorrecto genera error."""
        await client.post("/api/v1/auth/register", json=TEST_PASSENGER)

        response = await client.post(
            "/api/v1/auth/verify-phone",
            json={"phone_number": TEST_PASSENGER["phone_number"], "code": "000000"},
        )

        assert response.status_code == 400


class TestLogin:
    """Tests para el endpoint de login."""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient):
        """Verifica que el login funciona con credenciales correctas."""
        await register_and_verify(client, TEST_PASSENGER)

        response = await client.post(
            "/api/v1/auth/login",
            json={"phone_number": TEST_PASSENGER["phone_number"], "password": TEST_PASSENGER["password"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient):
        """Verifica que una contraseña incorrecta genera error."""
        await register_and_verify(client, TEST_PASSENGER)

        response = await client.post(
            "/api/v1/auth/login",
            json={"phone_number": TEST_PASSENGER["phone_number"], "password": "wrongpassword"},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_unverified_phone(self, client: AsyncClient):
        """Verifica que no se puede login sin verificar el teléfono."""
        await client.post("/api/v1/auth/register", json=TEST_PASSENGER)

        response = await client.post(
            "/api/v1/auth/login",
            json={"phone_number": TEST_PASSENGER["phone_number"], "password": TEST_PASSENGER["password"]},
        )

        assert response.status_code == 401
        assert "verificar" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Verifica que no se puede login con usuario inexistente."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"phone_number": "+51999999999", "password": "password123"},
        )

        assert response.status_code == 401


class TestProfile:
    """Tests para el endpoint de perfil."""

    @pytest.mark.asyncio
    async def test_get_profile_authenticated(self, client: AsyncClient):
        """Verifica que el perfil se obtiene con token válido."""
        await register_and_verify(client, TEST_PASSENGER)

        login_response = await client.post(
            "/api/v1/auth/login",
            json={"phone_number": TEST_PASSENGER["phone_number"], "password": TEST_PASSENGER["password"]},
        )
        token = login_response.json()["access_token"]

        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == TEST_PASSENGER["full_name"]
        assert data["phone_verified"] is True

    @pytest.mark.asyncio
    async def test_get_profile_no_token(self, client: AsyncClient):
        """Verifica que sin token se rechaza el acceso."""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_profile_invalid_token(self, client: AsyncClient):
        """Verifica que con token inválido se rechaza el acceso."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token_here"},
        )

        assert response.status_code == 401


class TestRefreshToken:
    """Tests para refresh token."""

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, client: AsyncClient):
        """Verifica que se puede obtener un nuevo access token."""
        await register_and_verify(client, TEST_PASSENGER)

        login_response = await client.post(
            "/api/v1/auth/login",
            json={"phone_number": TEST_PASSENGER["phone_number"], "password": TEST_PASSENGER["password"]},
        )
        refresh_token = login_response.json()["refresh_token"]

        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        assert "access_token" in response.json()

    @pytest.mark.asyncio
    async def test_refresh_invalid_token(self, client: AsyncClient):
        """Verifica que con token inválido se rechaza el refresh."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid_token"},
        )

        assert response.status_code == 401