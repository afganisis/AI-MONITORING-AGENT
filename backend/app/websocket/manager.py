"""
WebSocket connection manager for broadcasting real-time events.
"""

from typing import List, Dict, Any
from fastapi import WebSocket
from loguru import logger
import json


class WebSocketManager:
    """
    Manages WebSocket connections and broadcasts events.

    Features:
    - Multiple client connections
    - Broadcast to all connected clients
    - Automatic cleanup of disconnected clients
    - JSON message serialization
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """
        Accept new WebSocket connection.

        Args:
            websocket: WebSocket connection to add
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected, total connections: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        """
        Remove WebSocket connection.

        Args:
            websocket: WebSocket connection to remove
        """
        try:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected, total connections: {len(self.active_connections)}")
        except ValueError:
            logger.warning("Attempted to disconnect non-existent WebSocket")

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """
        Send message to specific client.

        Args:
            message: Message dictionary to send
            websocket: Target WebSocket connection
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
            await self.disconnect(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        """
        Broadcast message to all connected clients.

        Args:
            message: Message dictionary to broadcast

        The message should have the format:
        {
            "type": "event_type",
            "data": { ... event data ... }
        }

        Event types:
        - error_discovered: New error found
        - fix_started: Fix execution began
        - fix_success: Fix completed successfully
        - fix_failed: Fix failed
        - agent_status: Agent state changed
        - stats_update: Statistics updated
        """
        if not self.active_connections:
            logger.debug("No active connections to broadcast to")
            return

        logger.debug(f"Broadcasting {message.get('type')} to {len(self.active_connections)} clients")

        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to client: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            await self.disconnect(conn)

    async def broadcast_error_discovered(self, error_data: Dict[str, Any]):
        """
        Broadcast error discovered event.

        Args:
            error_data: Error details (id, key, severity, driver_id, etc.)
        """
        await self.broadcast({
            "type": "error_discovered",
            "data": error_data
        })

    async def broadcast_fix_started(self, fix_data: Dict[str, Any]):
        """
        Broadcast fix started event.

        Args:
            fix_data: Fix details (error_id, strategy_name, etc.)
        """
        await self.broadcast({
            "type": "fix_started",
            "data": fix_data
        })

    async def broadcast_fix_success(self, fix_data: Dict[str, Any]):
        """
        Broadcast fix success event.

        Args:
            fix_data: Fix result details
        """
        await self.broadcast({
            "type": "fix_success",
            "data": fix_data
        })

    async def broadcast_fix_failed(self, fix_data: Dict[str, Any]):
        """
        Broadcast fix failed event.

        Args:
            fix_data: Fix failure details
        """
        await self.broadcast({
            "type": "fix_failed",
            "data": fix_data
        })

    async def broadcast_agent_status(self, status_data: Dict[str, Any]):
        """
        Broadcast agent status change.

        Args:
            status_data: Agent status (state, config, etc.)
        """
        await self.broadcast({
            "type": "agent_status",
            "data": status_data
        })

    async def broadcast_stats_update(self, stats_data: Dict[str, Any]):
        """
        Broadcast statistics update.

        Args:
            stats_data: Updated statistics
        """
        await self.broadcast({
            "type": "stats_update",
            "data": stats_data
        })

    def get_connection_count(self) -> int:
        """Get number of active connections."""
        return len(self.active_connections)


# Global WebSocket manager instance
ws_manager = WebSocketManager()


def get_ws_manager() -> WebSocketManager:
    """Get global WebSocket manager instance."""
    return ws_manager
