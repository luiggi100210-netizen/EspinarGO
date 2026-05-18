"""
Configuración central del proyecto EspinarGo.

Este módulo contiene la clase Settings que carga todas las variables de
entorno del archivo .env y las valida automáticamente con Pydantic.
Si falta una variable obligatoria, la aplicación no arrancará.

Es la única fuente de verdad de configuración. Ningún otro archivo
debe leer variables de entorno directamente.
"""

from functools import lru_cache
from typing import List, Literal, Optional

from pydantic import EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuración global de la aplicación.

    Lee todas las variables de entorno del archivo .env y las valida.
    Cada variable tiene un tipo específico y valores por defecto razonables.

    Uso:
        from app.core.config import settings
        print(settings.APP_NAME)
    """

    # =====================================================================
    # APP - Configuración general
    # =====================================================================
    APP_NAME: str = "EspinarGo API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False
    SECRET_KEY: str
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # =====================================================================
    # DATABASE - Configuración de PostgreSQL
    # =====================================================================
    DATABASE_URL: str
    DATABASE_URL_SYNC: str

    # =====================================================================
    # REDIS - Configuración de cache y sesiones
    # =====================================================================
    REDIS_URL: str = "redis://localhost:6379/0"

    # =====================================================================
    # JWT - Configuración de tokens de autenticación
    # =====================================================================
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # =====================================================================
    # OTP - Configuración de códigos SMS (Twilio)
    # =====================================================================
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str
    OTP_EXPIRE_MINUTES: int = 10
    OTP_MAX_ATTEMPTS: int = 3
    OTP_RATE_LIMIT_PER_HOUR: int = 5

    # =====================================================================
    # EMAIL - Configuración de emails transaccionales (Resend)
    # =====================================================================
    RESEND_API_KEY: str
    FROM_EMAIL: EmailStr = "noreply@espinargo.com"
    FROM_NAME: str = "EspinarGo"

    # =====================================================================
    # CLOUDINARY - Configuración de almacenamiento en la nube
    # =====================================================================
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str

    # =====================================================================
    # OAUTH - Configuración de login social (opcionales)
    # =====================================================================
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    FACEBOOK_APP_ID: str = ""
    FACEBOOK_APP_SECRET: str = ""

    # =====================================================================
    # FIREBASE - Push notifications (opcional)
    # =====================================================================
    FIREBASE_CREDENTIALS_JSON: str = ""

    # =====================================================================
    # SENTRY - Configuración de monitoreo de errores (opcional)
    # =====================================================================
    SENTRY_DSN: str = ""

    # =====================================================================
    # Configuración del modelo Pydantic
    # =====================================================================
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # =====================================================================
    # Propiedades calculadas para verificar el entorno
    # =====================================================================
    @property
    def is_production(self) -> bool:
        """Retorna True si el entorno es production."""
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        """Retorna True si el entorno es development."""
        return self.ENVIRONMENT == "development"

    @property
    def is_staging(self) -> bool:
        """Retorna True si el entorno es staging."""
        return self.ENVIRONMENT == "staging"


@lru_cache()
def get_settings() -> Settings:
    """
    Retorna una instancia única de Settings (patrón Singleton).

    El decorador @lru_cache() caching el resultado, evitando que se
    lea el archivo .env en cada request. Esto mejora el rendimiento.

    Uso con FastAPI:
        from fastapi import Depends

        def my_endpoint(settings: Settings = Depends(get_settings)):
            print(settings.APP_NAME)

    Returns:
        Settings: Instancia única de configuración
    """
    return Settings()


# Instancia global para importación directa
settings = get_settings()