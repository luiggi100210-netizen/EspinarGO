"""
Router principal que agrupa todos los sub-routers de la API v1.

Rutas finales:
/api/v1/auth/...
/api/v1/users/...
/api/v1/trips/...
/api/v1/packages/...
/api/v1/ratings/...
/api/v1/admin/...
/ws/driver
/ws/trips/{trip_id}
"""

from fastapi import APIRouter

from app.api.v1.endpoints import admin, auth, packages, ratings, trips, users, ws

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(trips.router)
api_router.include_router(packages.router)
api_router.include_router(ratings.router)
api_router.include_router(admin.router)
api_router.include_router(ws.router)