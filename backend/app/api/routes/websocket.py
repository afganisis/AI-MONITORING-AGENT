"""
WebSocket endpoint for real-time client updates.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from ...websocket.manager import ws_manager


router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates.

    Clients connect to ws://localhost:8000/ws to receive:
    - error_discovered: New errors found
    - fix_started: Fix execution began
    - fix_success: Fix completed
    - fix_failed: Fix failed
    - agent_status: Agent state changes
    - stats_update: Statistics updates

    The connection is kept alive with periodic messages.
    """
    await ws_manager.connect(websocket)

    try:
        # Send initial connection success message
        await ws_manager.send_personal_message(
            {
                "type": "connected",
                "data": {
                    "message": "WebSocket connected successfully",
                    "connection_count": ws_manager.get_connection_count()
                }
            },
            websocket
        )

        # Keep connection alive and listen for client messages
        while True:
            # Receive messages from client (keep-alive pings)
            data = await websocket.receive_text()

            # Echo back for keep-alive
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected normally")
        await ws_manager.disconnect(websocket)

    except Exception as e:
        logger.exception(f"WebSocket error: {e}")
        await ws_manager.disconnect(websocket)
