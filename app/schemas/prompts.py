"""
Schemas for OPIK Prompt Versioning System
"""
from typing import List, Optional, Dict, Any
from pydantic import Field, validator
from datetime import datetime

from app.schemas.base import BaseSchema

class PromptTemplate(BaseSchema):
    """Schema for prompt templates"""
    name: str = Field(..., description="Name of the prompt template")
    description: str = Field(..., description="Description of what this prompt template is used for")
    template: str = Field(..., description="The prompt template with placeholders for variables")
    variables: List[str] = Field(default_factory=list, description="Variables used in the template")
    tags: List[str] = Field(default_factory=list, description="Tags to categorize the prompt template")
    
    @validator('variables', pre=True)
    def extract_variables(cls, v, values):
        """Extract variables from template if not provided"""
        if not v and "template" in values:
            # Simple extraction of variables in the format {variable_name}
            import re
            v = re.findall(r'\{([^{}]+)\}', values["template"])
        return v
    
    class Config:
        """Pydantic model config"""
        json_schema_extra = {
            "example": {
                "name": "character_dialogue",
                "description": "Template for generating character dialogue responses",
                "template": "You are {character_name}, {character_description}. Respond to: {user_input}",
                "variables": ["character_name", "character_description", "user_input"],
                "tags": ["dialogue", "character", "response"]
            }
        }

class PromptVersion(BaseSchema):
    """Schema for versioned prompts"""
    prompt_template_id: str = Field(..., description="The ID of the parent prompt template")
    version: str = Field(..., description="Version identifier (e.g., 'v1.0.0')")
    template: str = Field(..., description="The specific version of the prompt template")
    variables: List[str] = Field(default_factory=list, description="Variables used in this version")
    changes: str = Field("", description="Description of changes from previous version")
    performance_metrics: Dict[str, Any] = Field(default_factory=dict, description="Performance metrics")
    is_active: bool = Field(True, description="Whether this version is active")
    
    class Config:
        """Pydantic model config"""
        json_schema_extra = {
            "example": {
                "prompt_template_id": "123e4567-e89b-12d3-a456-426614174000",
                "version": "v1.0.0",
                "template": "You are {character_name}, {character_description}. Respond in a {tone} tone to: {user_input}",
                "variables": ["character_name", "character_description", "tone", "user_input"],
                "changes": "Added tone parameter to control character response style",
                "performance_metrics": {
                    "avg_response_quality": 4.2,
                    "avg_character_consistency": 3.9
                },
                "is_active": True
            }
        }

class PromptExperiment(BaseSchema):
    """Schema for prompt experiments"""
    name: str = Field(..., description="Name of the experiment")
    description: str = Field(..., description="Description of the experiment")
    prompt_versions: List[str] = Field(..., description="List of prompt version IDs in the experiment")
    metrics: List[str] = Field(..., description="List of metrics to track")
    start_date: datetime = Field(default_factory=datetime.utcnow, description="Start date of the experiment")
    end_date: Optional[datetime] = Field(None, description="End date of the experiment")
    status: str = Field("active", description="Status of the experiment (active, completed, cancelled)")
    results: Dict[str, Any] = Field(default_factory=dict, description="Results of the experiment")
    
    class Config:
        """Pydantic model config"""
        json_schema_extra = {
            "example": {
                "name": "Tone variation experiment",
                "description": "Testing different character tones for player engagement",
                "prompt_versions": [
                    "123e4567-e89b-12d3-a456-426614174001",
                    "123e4567-e89b-12d3-a456-426614174002"
                ],
                "metrics": ["user_engagement", "response_quality", "character_consistency"],
                "status": "active"
            }
        } 