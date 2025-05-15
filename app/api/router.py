"""
API Router to include all API endpoints
"""
from fastapi import APIRouter

from app.api.endpoints import dialogue, prompts, knowledge, memory, evaluation
from app.api import websocket

# Create API router
api_router = APIRouter()

# Include all routers
api_router.include_router(dialogue.router)
api_router.include_router(prompts.router)
api_router.include_router(knowledge.router)
api_router.include_router(memory.router)
api_router.include_router(evaluation.router)
api_router.include_router(websocket.router) 