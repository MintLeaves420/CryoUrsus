import logging
from typing import Dict, Set
from fastapi import WebSocket

logger = logging.getLogger("cryoursus.websocket")

class ConnectionManager:
    def __init__(self):
        # Maps shipment_id -> Set of WebSocket connections
        self._shipment_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, shipment_id: str, websocket: WebSocket):
        await websocket.accept()
        if shipment_id not in self._shipment_connections:
            self._shipment_connections[shipment_id] = set()
        self._shipment_connections[shipment_id].add(websocket)
        logger.info("Client connected to shipment %s (active: %d)", shipment_id, len(self._shipment_connections[shipment_id]))

    def disconnect(self, shipment_id: str, websocket: WebSocket):
        if shipment_id in self._shipment_connections:
            self._shipment_connections[shipment_id].discard(websocket)
            if not self._shipment_connections[shipment_id]:
                del self._shipment_connections[shipment_id]
        logger.info("Client disconnected from shipment %s", shipment_id)

    def get_subscriber_count(self, shipment_id: str) -> int:
        return len(self._shipment_connections.get(shipment_id, set()))

    async def broadcast(self, shipment_id: str, message: dict):
        if shipment_id not in self._shipment_connections:
            return
        dead_connections = set()
        for websocket in self._shipment_connections[shipment_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.warning("Failed to send message to websocket: %s", str(e))
                dead_connections.add(websocket)
        for dead in dead_connections:
            self.disconnect(shipment_id, dead)

ws_manager = ConnectionManager()
