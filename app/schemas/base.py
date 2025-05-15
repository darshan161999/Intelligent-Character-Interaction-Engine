"""
Base schema models
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, model_validator
import uuid

class BaseSchema(BaseModel):
    """Base schema with common fields"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @model_validator(mode='before')
    @classmethod
    def set_updated_at(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Set updated_at to current time"""
        if isinstance(data, dict):
            data["updated_at"] = datetime.utcnow()
        return data
        
    class Config:
        """Pydantic model config"""
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        } 