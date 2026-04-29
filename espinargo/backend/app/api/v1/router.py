"""
Router principal que agrupa todos los sub-routers de la API v1.

Este archivo es el mapa de toda la API. Para agregar nuevos módulos,
solo se añade aquí un nuevo include_router.

Rutas finales:
/api/v1/auth/...
/api/v1/users/...
/api/v1/trips/...
/api/v1/packages/...
/api/v1/ratings/...
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, packages, ratings, trips, users

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(trips.router)
api_router.include_router(packages.router)
api_router.include_router(ratings.router)