"""
Gestor de conexiones WebSocket.

Mantiene el estado de todas las conexiones activas:
- _drivers: conductores conectados (reciben viajes, envían ubicación)
- _trips: suscriptores al estado de un viaje específico (pasajero + conductor)
"""

from uuid import UUID

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._drivers: dict[UUID, WebSocket] = {}
        self._trips: dict[UUID, list[WebSocket]] = {}

    # ─── Conductores ─────────────────────────────────────────────────────────

    async def connect_driver(self, driver_id: UUID, ws: WebSocket) -> None:
        await ws.accept()
        self._drivers[driver_id] = ws

    def disconnect_driver(self, driver_id: UUID) -> None:
        self._drivers.pop(driver_id, None)

    async def broadcast_to_drivers(self, message: dict) -> None:
        dead: list[UUID] = []
        for driver_id, ws in self._drivers.items():
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(driver_id)
        for d in dead:
            self._drivers.pop(d, None)

    async def send_to_driver(self, driver_id: UUID, message: dict) -> None:
        ws = self._drivers.get(driver_id)
        if not ws:
            return
        try:
            await ws.send_json(message)
        except Exception:
            self._drivers.pop(driver_id, None)

    # ─── Seguimiento de viajes ────────────────────────────────────────────────

    async def connect_trip(self, trip_id: UUID, ws: WebSocket) -> None:
        await ws.accept()
        self._trips.setdefault(trip_id, []).append(ws)

    def disconnect_trip(self, trip_id: UUID, ws: WebSocket) -> None:
        connections = self._trips.get(trip_id, [])
        if ws in connections:
            connections.remove(ws)
        if not connections:
            self._trips.pop(trip_id, None)

    async def broadcast_to_trip(self, trip_id: UUID, message: dict) -> None:
        connections = self._trips.get(trip_id, [])
        dead: list[WebSocket] = []
        for ws in connections:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            connections.remove(ws)


manager = ConnectionManager()
