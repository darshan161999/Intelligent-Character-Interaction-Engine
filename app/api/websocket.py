"""
WebSocket API for real-time communication
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
import uuid
from typing import Optional, Dict, Any

from app.db.mongodb import get_async_db
from app.services.websocket import websocket_manager

router = APIRouter(prefix="/ws", tags=["websocket"])

@router.websocket("/connect")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: Optional[str] = Query(None),
    client_id: Optional[str] = Query(None),
    db: AsyncIOMotorDatabase = Depends(get_async_db)
):
    """
    WebSocket connection endpoint
    """
    # Accept the connection and register the client
    client_id = await websocket_manager.connect(
        websocket, 
        client_id=client_id,
        user_id=user_id,
        metadata={
            "user_agent": websocket.headers.get("user-agent", ""),
            "origin": websocket.headers.get("origin", "")
        }
    )
    
    # Welcome message
    await websocket.send_json({
        "event_type": "connection_established",
        "data": {
            "client_id": client_id,
            "message": "Connected to Hero Agent backend"
        }
    })
    
    try:
        # Listen for messages from the client
        await websocket_manager.listen_for_messages(websocket, client_id, db)
    except WebSocketDisconnect:
        # Handle disconnect
        websocket_manager.disconnect(client_id)
    except Exception as e:
        # Handle errors
        websocket_manager.disconnect(client_id)
        print(f"WebSocket error: {str(e)}")

@router.post("/send-event")
async def send_event(
    client_id: str,
    event_type: str,
    data: Dict[str, Any],
    sender_id: Optional[str] = None,
    target_ids: Optional[list] = None,
    db: AsyncIOMotorDatabase = Depends(get_async_db)
):
    """
    Send an event to a specific client via HTTP
    """
    # Check if client exists
    if client_id not in websocket_manager.active_connections:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Create event
    event = {
        "event_type": event_type,
        "data": data,
        "sender_id": sender_id,
        "target_ids": target_ids
    }
    
    # Send event
    success = await websocket_manager.send_event(client_id, event)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send event")
    
    return {"status": "success", "message": "Event sent"}

@router.post("/broadcast")
async def broadcast_event(
    event_type: str,
    data: Dict[str, Any],
    sender_id: Optional[str] = None,
    exclude: Optional[list] = None,
    db: AsyncIOMotorDatabase = Depends(get_async_db)
):
    """
    Broadcast an event to all connected clients via HTTP
    """
    # Create event
    event = {
        "event_type": event_type,
        "data": data,
        "sender_id": sender_id
    }
    
    # Broadcast event
    recipients = await websocket_manager.broadcast_event(event, exclude)
    
    return {
        "status": "success", 
        "message": f"Event broadcast to {len(recipients)} clients",
        "recipients": recipients
    }

@router.get("/connections")
async def get_active_connections():
    """
    Get all active WebSocket connections
    """
    connections = []
    for client_id, connection in websocket_manager.connection_metadata.items():
        connections.append({
            "client_id": client_id,
            "user_id": connection.user_id,
            "connected_at": connection.connected_at,
            "last_activity": connection.last_activity
        })
    
    return {
        "active_connections": len(connections),
        "connections": connections
    } 