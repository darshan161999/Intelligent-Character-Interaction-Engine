"""
WebSocket Service for managing real-time connections and events
"""
from typing import Dict, Set, List, Any, Optional, Callable, Awaitable
import asyncio
import json
from datetime import datetime
import uuid
from fastapi import WebSocket, WebSocketDisconnect
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.websocket import WebSocketConnection, WebSocketEvent, ChatEvent, ProximityEvent
from app.schemas.dialogue import DialogueRequest
from app.services.dialogue import dialogue_service

# Custom event handler type
EventHandler = Callable[[WebSocketEvent, AsyncIOMotorDatabase], Awaitable[None]]

class WebSocketManager:
    """Manager for WebSocket connections and events"""
    
    def __init__(self):
        """Initialize the WebSocket manager"""
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_metadata: Dict[str, WebSocketConnection] = {}
        self.event_handlers: Dict[str, List[EventHandler]] = {}
    
    async def connect(
        self,
        websocket: WebSocket,
        client_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Register a new WebSocket connection
        
        Args:
            websocket: The WebSocket connection
            client_id: Optional client ID (generated if not provided)
            user_id: Optional user ID for authentication
            metadata: Optional metadata for the connection
            
        Returns:
            The client ID
        """
        await websocket.accept()
        
        # Generate client ID if not provided
        if not client_id:
            client_id = str(uuid.uuid4())
        
        # Store connection
        self.active_connections[client_id] = websocket
        
        # Create and store connection metadata
        connection = WebSocketConnection(
            client_id=client_id,
            user_id=user_id,
            metadata=metadata or {}
        )
        self.connection_metadata[client_id] = connection
        
        return client_id
    
    def disconnect(self, client_id: str) -> None:
        """
        Unregister a WebSocket connection
        
        Args:
            client_id: The client ID to disconnect
        """
        if client_id in self.active_connections:
            self.active_connections.pop(client_id, None)
            self.connection_metadata.pop(client_id, None)
    
    async def send_event(self, client_id: str, event: WebSocketEvent) -> bool:
        """
        Send an event to a specific client
        
        Args:
            client_id: The client ID to send to
            event: The event to send
            
        Returns:
            True if sent successfully, False otherwise
        """
        if client_id not in self.active_connections:
            return False
        
        try:
            # Convert event to JSON and send
            await self.active_connections[client_id].send_json(event.dict())
            
            # Update last activity
            if client_id in self.connection_metadata:
                self.connection_metadata[client_id].last_activity = datetime.utcnow()
            
            return True
        except Exception:
            # If error occurs, assume connection is dead
            self.disconnect(client_id)
            return False
    
    async def broadcast_event(
        self,
        event: WebSocketEvent,
        exclude: Optional[List[str]] = None
    ) -> List[str]:
        """
        Broadcast an event to all connected clients
        
        Args:
            event: The event to broadcast
            exclude: Optional list of client IDs to exclude
            
        Returns:
            List of client IDs that received the event
        """
        exclude_set = set(exclude or [])
        sent_to = []
        
        # Send to all connections except excluded ones
        for client_id in list(self.active_connections.keys()):
            if client_id not in exclude_set:
                success = await self.send_event(client_id, event)
                if success:
                    sent_to.append(client_id)
        
        return sent_to
    
    async def handle_received_event(
        self,
        event: WebSocketEvent,
        db: AsyncIOMotorDatabase
    ) -> None:
        """
        Process a received event
        
        Args:
            event: The received event
            db: AsyncIOMotorDatabase instance
        """
        # Update metadata if sender is known
        if event.sender_id in self.connection_metadata:
            self.connection_metadata[event.sender_id].last_activity = datetime.utcnow()
        
        # Handle event based on type
        event_type = event.event_type
        
        # Check if there are any handlers for this event type
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                await handler(event, db)
        
        # Handle specific event types
        if event_type == "chat":
            await self._handle_chat_event(event, db)
        elif event_type == "proximity":
            await self._handle_proximity_event(event, db)
    
    async def _handle_chat_event(self, event: WebSocketEvent, db: AsyncIOMotorDatabase) -> None:
        """Handle chat events"""
        # Ensure it's a proper chat event
        if event.event_type != "chat" or "message" not in event.data:
            return
        
        # Extract message data
        message_data = event.data.get("message", {})
        content = message_data.get("content", "")
        
        # If targeting specific characters, generate responses
        if event.target_ids:
            for character_id in event.target_ids:
                # Create dialogue request
                request = DialogueRequest(
                    character_id=character_id,
                    user_message=content,
                    conversation_id=event.data.get("conversation_id"),
                    context=event.data.get("context", {})
                )
                
                # Generate response
                response = await dialogue_service.generate_dialogue(db, request)
                
                # Create response event
                response_event = ChatEvent(
                    data={
                        "message": response.message.dict(),
                        "conversation_id": response.conversation_id
                    },
                    sender_id=character_id,
                    target_ids=[event.sender_id] if event.sender_id else None
                )
                
                # Send response to sender
                if event.sender_id:
                    await self.send_event(event.sender_id, response_event)
        
        # Forward message to other targets if any
        if event.target_ids and not event.data.get("private", False):
            # Forward to other clients if not private
            for client_id in event.target_ids:
                if client_id != event.sender_id and client_id in self.active_connections:
                    await self.send_event(client_id, event)
    
    async def _handle_proximity_event(self, event: WebSocketEvent, db: AsyncIOMotorDatabase) -> None:
        """Handle proximity events"""
        # Extract data
        data = event.data
        is_within_range = data.get("is_within_range", False)
        
        # If a player is near a character, notify the player
        if is_within_range and "character_id" in data and "player_id" in data:
            character_id = data.get("character_id")
            player_id = data.get("player_id")
            
            # Create notification event for player
            notification = WebSocketEvent(
                event_type="character_proximity",
                data={
                    "character_id": character_id,
                    "is_within_range": True,
                    "distance": data.get("distance", 0),
                    "location": data.get("location", {})
                },
                sender_id=character_id,
                target_ids=[player_id]
            )
            
            # Send to player
            await self.send_event(player_id, notification)
    
    def register_event_handler(self, event_type: str, handler: EventHandler) -> None:
        """
        Register a handler for a specific event type
        
        Args:
            event_type: The event type to handle
            handler: The handler function
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(handler)
    
    def get_connection_info(self, client_id: str) -> Optional[WebSocketConnection]:
        """
        Get information about a connection
        
        Args:
            client_id: The client ID
            
        Returns:
            Connection information or None if not found
        """
        return self.connection_metadata.get(client_id)
    
    def get_connections_by_metadata(
        self,
        key: str,
        value: Any
    ) -> List[WebSocketConnection]:
        """
        Find connections by metadata
        
        Args:
            key: Metadata key to match
            value: Value to match
            
        Returns:
            List of matching connections
        """
        matches = []
        for conn in self.connection_metadata.values():
            if key in conn.metadata and conn.metadata[key] == value:
                matches.append(conn)
        return matches
    
    async def listen_for_messages(
        self,
        websocket: WebSocket,
        client_id: str,
        db: AsyncIOMotorDatabase
    ) -> None:
        """
        Listen for messages from a WebSocket connection
        
        Args:
            websocket: The WebSocket connection
            client_id: The client ID
            db: AsyncIOMotorDatabase instance
        """
        try:
            while True:
                # Receive JSON data
                data = await websocket.receive_json()
                
                try:
                    # Add client_id as sender if not specified
                    if "sender_id" not in data:
                        data["sender_id"] = client_id
                    
                    # Convert to event object based on type
                    event_type = data.get("event_type", "")
                    
                    if event_type == "chat":
                        event = ChatEvent(**data)
                    elif event_type == "proximity":
                        event = ProximityEvent(**data)
                    else:
                        event = WebSocketEvent(**data)
                    
                    # Handle the event
                    await self.handle_received_event(event, db)
                
                except Exception as e:
                    # Send error message back to client
                    await websocket.send_json({
                        "event_type": "error",
                        "data": {
                            "message": f"Error processing event: {str(e)}",
                            "original_data": data
                        }
                    })
        
        except WebSocketDisconnect:
            # Handle disconnect
            self.disconnect(client_id)
        
        except Exception:
            # Handle any other exception
            self.disconnect(client_id)

# Create a singleton instance
websocket_manager = WebSocketManager() 