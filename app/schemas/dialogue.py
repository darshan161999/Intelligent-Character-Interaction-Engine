"""
Schemas for character dialogue interactions
"""
from typing import List, Optional, Dict, Any, Literal
from pydantic import Field, validator
from datetime import datetime

from app.schemas.base import BaseSchema

class Message(BaseSchema):
    """Schema for a single message in a conversation"""
    role: Literal["user", "assistant", "system"] = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Content of the message")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata for the message")
    
    class Config:
        """Pydantic model config"""
        json_schema_extra = {
            "example": {
                "role": "assistant",
                "content": "Greetings, fellow Avenger! What brings you to Stark Tower today?",
                "metadata": {
                    "character": "Iron Man",
                    "emotion": "friendly",
                    "prompt_version_id": "123e4567-e89b-12d3-a456-426614174000"
                }
            }
        }

class Conversation(BaseSchema):
    """Schema for a conversation between characters or character and player"""
    participant_ids: List[str] = Field(..., description="IDs of conversation participants")
    messages: List[Message] = Field(default_factory=list, description="Messages in the conversation")
    is_active: bool = Field(True, description="Whether the conversation is active")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata for the conversation")
    
    class Config:
        """Pydantic model config"""
        json_schema_extra = {
            "example": {
                "participant_ids": ["player_123", "character_iron_man"],
                "is_active": True,
                "metadata": {
                    "location": "Stark Tower",
                    "context": "First meeting",
                    "game_session_id": "session_456"
                }
            }
        }

class DialogueRequest(BaseSchema):
    """Schema for requesting a dialogue generation"""
    character_id: str = Field(..., description="ID of the character generating dialogue")
    user_message: str = Field(..., description="User's message to respond to")
    conversation_id: Optional[str] = Field(None, description="ID of existing conversation")
    prompt_version_id: Optional[str] = Field(None, description="Specific prompt version to use")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context for dialogue generation")
    
    class Config:
        """Pydantic model config"""
        json_schema_extra = {
            "example": {
                "character_id": "character_iron_man",
                "user_message": "What are you working on?",
                "conversation_id": "conv_123456",
                "context": {
                    "location": "Stark Tower Lab",
                    "current_project": "Mark 42 armor",
                    "mood": "focused"
                }
            }
        }

class DialogueResponse(BaseSchema):
    """Schema for dialogue generation response"""
    message: Message = Field(..., description="The generated message")
    conversation_id: str = Field(..., description="ID of the conversation")
    prompt_used: Dict[str, Any] = Field(default_factory=dict, description="Information about the prompt used")
    context_used: Dict[str, Any] = Field(default_factory=dict, description="Information about the context used")
    
    class Config:
        """Pydantic model config"""
        json_schema_extra = {
            "example": {
                "message": {
                    "role": "assistant",
                    "content": "I'm working on the new Mark 42 armor. It's going to be my most advanced suit yet, with modular components that I can call to me remotely.",
                    "metadata": {
                        "character": "Iron Man",
                        "emotion": "excited"
                    }
                },
                "conversation_id": "conv_123456",
                "prompt_used": {
                    "template_id": "character_dialogue",
                    "version_id": "v2.1.0"
                },
                "context_used": {
                    "knowledge_chunks_used": ["chunk_id_1", "chunk_id_2"],
                    "memory_used": ["memory_id_1"]
                }
            }
        } 