"""
Schemas for WebSocket communications
"""
from typing import List, Optional, Dict, Any, Literal
from pydantic import Field, root_validator
from datetime import datetime

from app.schemas.base import BaseSchema
from app.schemas.dialogue import Message

class WebSocketConnection(BaseSchema):
    """Schema for tracking an active WebSocket connection"""
    client_id: str = Field(..., description="Unique client ID")
    user_id: Optional[str] = Field(None, description="User ID if authenticated")
    connected_at: datetime = Field(default_factory=datetime.utcnow, description="Connection time")
    last_activity: datetime = Field(default_factory=datetime.utcnow, description="Last activity time")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Connection metadata")

class WebSocketEvent(BaseSchema):
    """Schema for WebSocket events"""
    event_type: str = Field(..., description="Type of the event")
    data: Dict[str, Any] = Field(default_factory=dict, description="Event data")
    sender_id: Optional[str] = Field(None, description="ID of the sender")
    target_ids: Optional[List[str]] = Field(None, description="IDs of the targets (None for broadcast)")
    
    class Config:
        """Pydantic model config"""
        json_schema_extra = {
            "example": {
                "event_type": "proximity",
                "data": {
                    "character_id": "character_iron_man",
                    "distance": 5.2,
                    "location": {"x": 100, "y": 200, "z": 0}
                },
                "sender_id": "player_123"
            }
        }

class ChatEvent(WebSocketEvent):
    """Schema for chat events over WebSocket"""
    event_type: Literal["chat"] = "chat"
    data: Dict[str, Any] = Field(..., description="Chat event data")
    
    @root_validator(pre=True)
    def ensure_message_in_data(cls, values):
        """Ensure message is in data"""
        if "data" in values and "message" not in values["data"]:
            if "content" in values:
                values["data"]["message"] = {
                    "content": values.pop("content"),
                    "role": values.pop("role", "user"),
                    "metadata": values.pop("metadata", {})
                }
        return values
    
    class Config:
        """Pydantic model config"""
        json_schema_extra = {
            "example": {
                "event_type": "chat",
                "data": {
                    "message": {
                        "role": "user",
                        "content": "Hello Iron Man, how are you?",
                        "metadata": {
                            "location": "Stark Tower"
                        }
                    },
                    "conversation_id": "conv_123456"
                },
                "sender_id": "player_123",
                "target_ids": ["character_iron_man"]
            }
        }

class ProximityEvent(WebSocketEvent):
    """Schema for proximity events over WebSocket"""
    event_type: Literal["proximity"] = "proximity"
    data: Dict[str, Any] = Field(..., description="Proximity event data")
    
    class Config:
        """Pydantic model config"""
        json_schema_extra = {
            "example": {
                "event_type": "proximity",
                "data": {
                    "character_id": "character_iron_man",
                    "player_id": "player_123",
                    "distance": 2.5,
                    "is_within_range": True,
                    "location": {"x": 120, "y": 80, "z": 0}
                },
                "sender_id": "player_123"
            }
        } 