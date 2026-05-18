"""
Gestor de conexiones WebSocket con Redis Pub/Sub.

Cada worker de uvicorn mantiene sus propias conexiones WebSocket en memoria.
La coordinación entre workers se hace vía Redis Pub/Sub:
- Al hacer broadcast, se publica en Redis.
- Un listener por worker recibe los mensajes de Redis y los reenvía
  a las conexiones locales de ese worker.

Esto permite escalar a múltiples workers sin perder mensajes.

Canales Redis:
  espinargo:ws:drivers          → broadcast a todos los conductores
  espinargo:ws:trip:{trip_id}   → broadcast a los suscritos a un viaje
  espinargo:ws:driver:{id}      → envío directo a un conductor
"""

import asyncio
import json
import logging
from uuid import UUID

import redis.asyncio as aioredis
from fastapi import WebSocket

from app.core.config import settings

logger = logging.getLogger(__name__)

_CH_DRIVERS = "espinargo:ws:drivers"
_CH_TRIP = "espinargo:ws:trip:"
_CH_DRIVER = "espinargo:ws:driver:"


class ConnectionManager:
    def __init__(self) -> None:
        self._drivers: dict[UUID, WebSocket] = {}
        self._trips: dict[UUID, list[WebSocket]] = {}
        self._redis: aioredis.Redis | None = None
        self._listener_task: asyncio.Task | None = None

    # ─── Lifecycle ────────────────────────────────────────────────────────────

    async def startup(self) -> None:
        """Conecta a Redis e inicia el listener de pub/sub. Llamar desde lifespan."""
        self._redis = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        self._listener_task = asyncio.create_task(self._listen())

    async def shutdown(self) -> None:
        """Cancela el listener y cierra la conexión Redis."""
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
        if self._redis:
            await self._redis.aclose()

    # ─── Redis listener ───────────────────────────────────────────────────────

    async def _listen(self) -> None:
        """
        Escucha todos los canales relevantes de Redis y reenvía los mensajes
        a las conexiones WebSocket locales de este worker.
        """
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(_CH_DRIVERS)
        await pubsub.psubscribe(f"{_CH_TRIP}*", f"{_CH_DRIVER}*")

        async for message in pubsub.listen():
            if message["type"] not in ("message", "pmessage"):
                continue
            try:
                channel: str = message["channel"]
                data: dict = json.loads(message["data"])

                if channel == _CH_DRIVERS:
                    await self._local_broadcast_to_drivers(data)
                elif channel.startswith(_CH_TRIP):
                    trip_id = UUID(channel[len(_CH_TRIP):])
                    await self._local_broadcast_to_trip(trip_id, data)
                elif channel.startswith(_CH_DRIVER):
                    driver_id = UUID(channel[len(_CH_DRIVER):])
                    await self._local_send_to_driver(driver_id, data)
            except Exception:
                logger.exception("Error procesando mensaje Redis en canal %s", message.get("channel"))

    # ─── Publish ──────────────────────────────────────────────────────────────

    async def _publish(self, channel: str, message: dict) -> None:
        if self._redis:
            await self._redis.publish(channel, json.dumps(message))

    # ─── Entrega local (solo conexiones de este worker) ───────────────────────

    async def _local_broadcast_to_drivers(self, message: dict) -> None:
        dead: list[UUID] = []
        for driver_id, ws in self._drivers.items():
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(driver_id)
        for d in dead:
            self._drivers.pop(d, None)

    async def _local_broadcast_to_trip(self, trip_id: UUID, message: dict) -> None:
        connections = self._trips.get(trip_id, [])
        dead: list[WebSocket] = []
        for ws in connections:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            connections.remove(ws)

    async def _local_send_to_driver(self, driver_id: UUID, message: dict) -> None:
        ws = self._drivers.get(driver_id)
        if not ws:
            return
        try:
            await ws.send_json(message)
        except Exception:
            self._drivers.pop(driver_id, None)

    # ─── API pública — Conductores ────────────────────────────────────────────

    def connect_driver(self, driver_id: UUID, ws: WebSocket) -> None:
        self._drivers[driver_id] = ws

    def disconnect_driver(self, driver_id: UUID) -> None:
        self._drivers.pop(driver_id, None)

    async def broadcast_to_drivers(self, message: dict) -> None:
        """Publica en Redis; todos los workers entregan a sus conductores locales."""
        await self._publish(_CH_DRIVERS, message)

    async def send_to_driver(self, driver_id: UUID, message: dict) -> None:
        """Publica en Redis; el worker que tiene al conductor lo entrega."""
        await self._publish(f"{_CH_DRIVER}{driver_id}", message)

    # ─── API pública — Viajes ─────────────────────────────────────────────────

    def connect_trip(self, trip_id: UUID, ws: WebSocket) -> None:
        self._trips.setdefault(trip_id, []).append(ws)

    def disconnect_trip(self, trip_id: UUID, ws: WebSocket) -> None:
        connections = self._trips.get(trip_id, [])
        if ws in connections:
            connections.remove(ws)
        if not connections:
            self._trips.pop(trip_id, None)

    async def broadcast_to_trip(self, trip_id: UUID, message: dict) -> None:
        """Publica en Redis; todos los workers entregan a sus suscritos locales."""
        await self._publish(f"{_CH_TRIP}{trip_id}", message)


manager = ConnectionManager()
