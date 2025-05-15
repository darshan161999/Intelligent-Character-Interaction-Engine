"""
Memory schemas for character long-term memory
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

from app.schemas.base import BaseSchema

class Memory(BaseSchema):
    """Memory schema"""
    character_id: str = Field(..., description="ID of the character this memory belongs to")
    content: str = Field(..., description="Content of the memory")
    source: str = Field("conversation", description="Source of the memory (conversation, wiki, etc.)")
    importance: int = Field(5, ge=1, le=10, description="Importance score (1-10)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    last_accessed: datetime = Field(default_factory=datetime.utcnow, description="Last access timestamp")
    access_count: int = Field(0, description="Number of times this memory has been accessed")

class MemoryCreate(BaseModel):
    """Schema for creating a new memory"""
    character_id: str = Field(..., description="ID of the character")
    content: str = Field(..., description="Content of the memory")
    source: str = Field("conversation", description="Source of the memory")
    importance: int = Field(5, ge=1, le=10, description="Importance score (1-10)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class MemoryUpdate(BaseModel):
    """Schema for updating a memory"""
    content: Optional[str] = Field(None, description="Updated content")
    importance: Optional[int] = Field(None, ge=1, le=10, description="Updated importance score")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated metadata")

class MemorySearch(BaseModel):
    """Schema for searching memories"""
    character_id: str = Field(..., description="ID of the character")
    query: str = Field(..., description="Search query")
    limit: int = Field(5, ge=1, le=20, description="Maximum number of results")

class MemoryResponse(BaseModel):
    """Schema for memory response"""
    id: str = Field(..., description="Memory ID")
    character_id: str = Field(..., description="Character ID")
    content: str = Field(..., description="Memory content")
    source: str = Field(..., description="Memory source")
    importance: int = Field(..., description="Importance score")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    last_accessed: datetime = Field(..., description="Last access timestamp")
    access_count: int = Field(..., description="Access count")
    relevance_score: Optional[float] = Field(None, description="Relevance score from search")

class MemorySearchResponse(BaseModel):
    """Schema for memory search response"""
    memories: List[MemoryResponse] = Field(..., description="List of memories")
    query: str = Field(..., description="Original search query")
    character_id: str = Field(..., description="Character ID") 