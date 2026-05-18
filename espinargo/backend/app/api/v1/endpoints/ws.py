"""
Endpoints WebSocket para comunicación en tiempo real.

/ws/driver           → Canal del conductor
/ws/trips/{trip_id}  → Seguimiento de un viaje específico
"""

import asyncio
import logging
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import decode_access_token
from app.models.trip import Trip, TripStatus
from app.models.user import User, UserRole, UserStatus
from app.websockets.manager import manager


def _parse_coord(value) -> float | None:
    """Convierte lat/lng a float; retorna None si no es un número válido."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

router = APIRouter(tags=["WebSocket"])


async def _authenticate(token: str) -> User | None:
    """Decodifica el JWT y retorna el usuario activo, o None si no es válido."""
    try:
        payload = decode_access_token(token)
        user_id = UUID(payload["sub"])
        async with AsyncSessionLocal() as db:
            user = await db.get(User, user_id)
        return user if user and user.status == UserStatus.ACTIVE else None
    except Exception:
        return None


@router.websocket("/ws/driver")
async def driver_ws(websocket: WebSocket):
    """
    Canal WebSocket exclusivo del conductor.

    El primer mensaje debe ser el handshake de autenticación:
        {"type": "auth", "token": "<access_token>"}

    Mensajes que el conductor envía al servidor:
        {"type": "location", "lat": "-14.832", "lng": "-71.013"}
        {"type": "online", "status": true}

    Mensajes que el conductor recibe del servidor:
        {"type": "new_trip", "trip": {...}}
        {"type": "offer_accepted", "trip_id": "uuid"}
        {"type": "trip_update", "trip_id": "uuid", "status": "cancelled"}
    """
    await websocket.accept()

    try:
        auth_msg = await asyncio.wait_for(websocket.receive_json(), timeout=10.0)
    except (asyncio.TimeoutError, ValueError, TypeError):
        await websocket.close(code=4001, reason="No autorizado")
        return

    token = auth_msg.get("token") if isinstance(auth_msg, dict) else None
    user = await _authenticate(token) if token else None

    if not user or user.role not in (UserRole.DRIVER, UserRole.ADMIN):
        await websocket.close(code=4001, reason="No autorizado")
        return

    manager.connect_driver(user.id, websocket)

    async with AsyncSessionLocal() as db:
        user_db = await db.get(User, user.id)
        if user_db and user_db.driver_profile:
            user_db.driver_profile.is_online = True
            await db.commit()

    try:
        while True:
            try:
                data = await websocket.receive_json()
            except (ValueError, KeyError):
                continue
            msg_type = data.get("type")

            if msg_type == "location":
                lat = _parse_coord(data.get("lat"))
                lng = _parse_coord(data.get("lng"))
                async with AsyncSessionLocal() as db:
                    user_db = await db.get(User, user.id)
                    if user_db and user_db.driver_profile:
                        if lat is not None:
                            user_db.driver_profile.current_lat = str(lat)
                        if lng is not None:
                            user_db.driver_profile.current_lng = str(lng)
                    result = await db.execute(
                        select(Trip)
                        .where(
                            Trip.driver_id == user.id,
                            Trip.status == TripStatus.IN_PROGRESS,
                        )
                        .limit(1)
                    )
                    active_trip = result.scalar_one_or_none()
                    await db.commit()

                if active_trip and lat is not None and lng is not None:
                    await manager.broadcast_to_trip(
                        active_trip.id,
                        {"type": "driver_location", "lat": lat, "lng": lng},
                    )

            elif msg_type == "online":
                async with AsyncSessionLocal() as db:
                    user_db = await db.get(User, user.id)
                    if user_db and user_db.driver_profile:
                        user_db.driver_profile.is_online = bool(data.get("status", True))
                        await db.commit()

    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("Error inesperado en driver_ws (user=%s)", user.id)
    finally:
        manager.disconnect_driver(user.id)
        async with AsyncSessionLocal() as db:
            user_db = await db.get(User, user.id)
            if user_db and user_db.driver_profile:
                user_db.driver_profile.is_online = False
                await db.commit()


@router.websocket("/ws/trips/{trip_id}")
async def trip_ws(trip_id: UUID, websocket: WebSocket):
    """
    Canal WebSocket para seguimiento de un viaje en tiempo real.

    El primer mensaje debe ser el handshake de autenticación:
        {"type": "auth", "token": "<access_token>"}

    Mensajes que el cliente recibe:
        {"type": "driver_location", "lat": "...", "lng": "..."}
        {"type": "new_offer", "offer_id": "uuid", "offered_price": "7.50", "driver_name": "..."}
        {"type": "offer_accepted", "trip_id": "uuid"}
        {"type": "trip_update", "status": "in_progress"}
    """
    await websocket.accept()

    try:
        auth_msg = await asyncio.wait_for(websocket.receive_json(), timeout=10.0)
    except (asyncio.TimeoutError, ValueError, TypeError):
        await websocket.close(code=4001, reason="No autorizado")
        return

    token = auth_msg.get("token") if isinstance(auth_msg, dict) else None
    user = await _authenticate(token) if token else None

    if not user:
        await websocket.close(code=4001, reason="No autorizado")
        return

    async with AsyncSessionLocal() as db:
        trip = await db.get(Trip, trip_id)

    if not trip:
        await websocket.close(code=4004, reason="Viaje no encontrado")
        return

    is_participant = (
        trip.passenger_id == user.id
        or trip.driver_id == user.id
        or user.role == UserRole.ADMIN
    )
    if not is_participant:
        await websocket.close(code=4003, reason="Acceso denegado")
        return

    manager.connect_trip(trip_id, websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("Error inesperado en trip_ws (trip=%s, user=%s)", trip_id, user.id)
    finally:
        manager.disconnect_trip(trip_id, websocket)
