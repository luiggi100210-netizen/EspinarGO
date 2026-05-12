"""
Punto de entrada principal de la aplicación FastAPI.

Este archivo une todo lo construido en los módulos anteriores:
- Configuración de la app FastAPI
- Middlewares (CORS, GZip)
- Rutas base (/, /health)
- Lifecycle (startup/shutdown)
- Manejadores de errores globales
"""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.api.v1.endpoints.ws import router as ws_router
from app.core.config import settings
from app.core.database import check_database_connection, engine
from app.websockets.manager import manager

# Importar todos los modelos para que SQLAlchemy los registre
# Estas importaciones son necesarias para que Base.metadata
# conozca todas las tablas al crear las migraciones
from app.models.user import DriverProfile, OTPCode, RefreshToken, User
from app.models.trip import Trip, TripOffer
from app.models.package import Package, PackageTracking
from app.models.rating import Rating


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Ciclo de vida de la aplicación.

    Ejecuta procesos al iniciar y al cerrar la app.
    """
    # STARTUP
    print(f"\n🚀 Iniciar {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"   Entorno: {settings.ENVIRONMENT}\n")

    db_connected = await check_database_connection()
    if db_connected:
        print("✅ Base de datos conectada")
    else:
        print("⚠️  Base de datos no conectada (Railway puede tardar en levantar)")

    await manager.startup()
    print("✅ WebSocket manager con Redis Pub/Sub iniciado")

    if settings.SENTRY_DSN and settings.is_production:
        import sentry_sdk

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            traces_sample_rate=0.1,
            environment=settings.ENVIRONMENT,
        )
        print("✅ Sentry configurado")

    if not settings.is_production:
        print(f"📚 Documentación: http://localhost:8000/docs\n")

    yield

    # SHUTDOWN
    print("\n🛑 Cerrando aplicación...")
    await manager.shutdown()
    await engine.dispose()
    print("✅ Conexiones de base de datos liberadas")


def create_app() -> FastAPI:
    """
    Construye y configura la aplicación FastAPI.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="""
# EspinarGo API

EspinarGo es una aplicación de transporte tipo InDrive para la ciudad de Espinar, Cusco, Perú. Permite a los pasajeros solicitar viajes y a los conductores aceptar ofertas de precio.

## Módulos Disponibles

- **Autenticación**: Registro, login, verificación OTP, recuperación de contraseña
- **Usuarios**: Perfiles de usuario y conductor, documentos, vehículo
- **Viajes**: Solicitar viaje, ofertas de precio, iniciar/completar/cancelar
- **Encomiendas**: Crear envío, rastrear, asignar conductor, actualizar estado
- **Calificaciones**: Calificar después de cada viaje

## Autenticación

La API usa autenticación con Bearer token JWT. Incluir en el header:
```
Authorization: Bearer <access_token>
```

El token expira en 30 minutos. Usar el endpoint `/auth/refresh` para renovarlo.

## Contacto

Para soporte técnico: soporte@espinargo.com
""",
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None if settings.is_production else "/redoc",
        openapi_url=None if settings.is_production else "/openapi.json",
        lifespan=lifespan,
    )

    # Middlewares
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(
        GZipMiddleware,
        minimum_size=1000,
    )

    # Incluir router principal
    app.include_router(api_router)
    app.include_router(ws_router)  # WebSocket en / (no bajo /api/v1)

    # Rutas base
    @app.get(
        "/",
        tags=["Root"],
        summary="Raíz de la API",
    )
    async def root() -> dict[str, Any]:
        return {
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "docs": "http://localhost:8000/docs" if not settings.is_production else None,
            "status": "running",
        }

    @app.get(
        "/health",
        tags=["Health Check"],
        summary="Verificar estado de la API",
    )
    async def health_check() -> JSONResponse:
        db_connected = await check_database_connection()

        content = {
            "status": "ok" if db_connected else "degraded",
            "database": "ok" if db_connected else "error",
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
        }

        return JSONResponse(
            status_code=200 if db_connected else 503,
            content=content,
        )

    # Manejadores de errores globales
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: Any) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={
                "detail": "Recurso no encontrado",
                "path": str(request.url),
            },
        )

    @app.exception_handler(500)
    async def internal_error_handler(request: Request, exc: Any) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Error interno del servidor. Intenta más tarde.",
            },
        )

    @app.exception_handler(422)
    async def validation_error_handler(request: Request, exc: Any) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Datos inválidos en la solicitud",
                "errors": exc.detail if hasattr(exc, "detail") else str(exc),
            },
        )

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        workers=1 if settings.is_development else 4,
    )