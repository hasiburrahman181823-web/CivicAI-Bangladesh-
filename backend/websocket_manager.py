"""
CivicAI Bangladesh - WebSocket Real-Time Event Hub
Maintains live connections with web clients and broadcasts real-time complaint updates.
"""

import json
from typing import List, Dict, Any
from fastapi import WebSocket

class WebSocketConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_event(self, event_type: str, data: Dict[str, Any]):
        """Broadcast structured event to all active connected browsers."""
        payload = json.dumps({
            "event": event_type,
            "data": data
        }, default=str)

        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception:
                disconnected.append(connection)

        for dead_conn in disconnected:
            self.disconnect(dead_conn)

ws_manager = WebSocketConnectionManager()
