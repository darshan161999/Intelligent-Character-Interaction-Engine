"""
Knowledge schemas for text chunks and vector embeddings
"""
from typing import List, Optional
from pydantic import Field

from app.schemas.base import BaseSchema

class KnowledgeChunk(BaseSchema):
    """Schema for a knowledge chunk with vector embedding"""
    source: str = Field(..., description="Source of the knowledge (e.g., Wikipedia article title)")
    content: str = Field(..., description="The text content of the chunk")
    vector_embedding: Optional[List[float]] = Field(None, description="Vector embedding of the content")
    metadata: dict = Field(default_factory=dict, description="Additional metadata for the chunk")
    
    class Config:
        """Pydantic model config"""
        json_schema_extra = {
            "example": {
                "source": "Iron Man (Character)",
                "content": "Tony Stark is a genius inventor and billionaire industrialist...",
                "metadata": {
                    "character": "Iron Man",
                    "topic": "origin",
                    "tags": ["avengers", "marvel", "technology"]
                }
            }
        }

class KnowledgeQuery(BaseSchema):
    """Schema for querying knowledge chunks"""
    query: str = Field(..., description="The query text to search for")
    top_k: int = Field(5, description="Number of results to return")
    filter_metadata: Optional[dict] = Field(None, description="Filter by metadata fields")
    
    class Config:
        """Pydantic model config"""
        json_schema_extra = {
            "example": {
                "query": "Tell me about Iron Man's suit technology",
                "top_k": 3,
                "filter_metadata": {
                    "character": "Iron Man",
                    "tags": ["technology"]
                }
            }
        } 