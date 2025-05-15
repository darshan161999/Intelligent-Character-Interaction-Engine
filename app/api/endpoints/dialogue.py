"""
Dialogue API for character interactions
"""
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId

from app.db.mongodb import get_async_db
from app.schemas.dialogue import DialogueRequest, DialogueResponse, Conversation, Message
from app.services.dialogue import dialogue_service
from app.core.langgraph_orchestration import generate_dialogue_response

router = APIRouter(prefix="/dialogue", tags=["dialogue"])

@router.post("/generate", response_model=DialogueResponse)
async def generate_dialogue(
    request: DialogueRequest,
    db: AsyncIOMotorDatabase = Depends(get_async_db)
):
    """
    Generate a dialogue response from a character
    """
    try:
        # Generate response using dialogue service
        response = await dialogue_service.generate_dialogue(db, request)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating dialogue response: {str(e)}"
        )

@router.post("/generate-with-langgraph")
async def generate_with_langgraph(
    request: DialogueRequest,
    db: AsyncIOMotorDatabase = Depends(get_async_db)
):
    """
    Generate a dialogue response using LangGraph orchestration
    """
    try:
        # Generate response using LangGraph
        result = await generate_dialogue_response(
            user_input=request.user_message,
            character_id=request.character_id,
            conversation_id=request.conversation_id,
            prompt_version_id=request.prompt_version_id,
            context=request.context
        )
        
        # Create message
        message = Message(
            role="assistant",
            content=result["response"],
            metadata={
                "character_id": request.character_id,
                "knowledge_used": result.get("knowledge_used", [])
            }
        )
        
        # Create response
        response = DialogueResponse(
            message=message,
            conversation_id=result.get("conversation_id") or "temp_conversation_id",
            prompt_used={
                "version_id": request.prompt_version_id or "default"
            },
            context_used={
                "knowledge_chunks_used": result.get("knowledge_used", [])
            }
        )
        
        return response
    
    except Exception as e:
        print(f"Error generating dialogue with LangGraph: {str(e)}")
        # Create fallback response in case of error
        message = Message(
            role="assistant",
            content=f"I'm sorry, but I'm having trouble responding right now. Error: {str(e)}",
            metadata={
                "error": str(e),
                "character_id": request.character_id
            }
        )
        
        return DialogueResponse(
            message=message,
            conversation_id="error_conversation",
            prompt_used={"version_id": "error"},
            context_used={}
        )

@router.get("/conversations", response_model=List[Dict[str, Any]])
async def get_conversations(
    character_id: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_async_db)
):
    """
    Get conversations, optionally filtered by character ID
    """
    try:
        # Query the database for conversations
        collection = db["conversations"]
        query = {}
        
        # Add character filter if provided
        if character_id:
            query["participant_ids"] = character_id
        
        # Execute query
        cursor = collection.find(query).sort("updated_at", -1).limit(limit)
        conversations = []
        
        async for conv in cursor:
            # Format the conversation for response
            conv_data = {
                "id": str(conv["_id"]),
                "participant_ids": conv.get("participant_ids", []),
                "is_active": conv.get("is_active", True),
                "message_count": len(conv.get("messages", [])),
                "last_message_at": conv.get("updated_at", conv.get("created_at", datetime.utcnow())).isoformat()
            }
            conversations.append(conv_data)
        
        return conversations
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving conversations: {str(e)}"
        )

@router.get("/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(
    conversation_id: str = Path(...),
    db: AsyncIOMotorDatabase = Depends(get_async_db)
):
    """
    Get a specific conversation by ID
    """
    try:
        # Convert string ID to ObjectId
        try:
            obj_id = ObjectId(conversation_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid conversation ID format")
        
        conversation = await dialogue_service.get_conversation(db, obj_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving conversation: {str(e)}"
        )

@router.post("/conversations/{conversation_id}/messages", response_model=Message)
async def add_message(
    message: Message,
    conversation_id: str = Path(...),
    db: AsyncIOMotorDatabase = Depends(get_async_db)
):
    """
    Add a message to a conversation
    """
    try:
        # Convert string ID to ObjectId
        try:
            obj_id = ObjectId(conversation_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid conversation ID format")
        
        # Check if conversation exists
        conversation = await dialogue_service.get_conversation(db, obj_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Add message to conversation
        success = await dialogue_service.add_message(db, obj_id, message)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to add message")
        
        return message
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error adding message: {str(e)}"
        )

@router.post("/conversations", response_model=Dict[str, str])
async def create_conversation(
    participant_ids: List[str],
    metadata: Optional[Dict[str, Any]] = None,
    db: AsyncIOMotorDatabase = Depends(get_async_db)
):
    """
    Create a new conversation
    """
    try:
        conversation_id = await dialogue_service.create_conversation(
            db, participant_ids, metadata
        )
        return {"conversation_id": conversation_id}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating conversation: {str(e)}"
        ) 