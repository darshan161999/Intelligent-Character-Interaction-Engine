"""
Memory API for character long-term memory
"""
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional

from app.db.mongodb import get_async_db
from app.schemas.memory import MemoryCreate, MemoryUpdate, MemorySearch, MemoryResponse, MemorySearchResponse
from app.memory.service import memory_service

router = APIRouter(prefix="/memory", tags=["memory"])

@router.post("/create", response_model=MemoryResponse)
async def create_memory(
    memory: MemoryCreate,
    db: AsyncIOMotorDatabase = Depends(get_async_db)
):
    """
    Create a new memory for a character
    """
    try:
        memory_id = await memory_service.create_memory(
            db,
            memory.character_id,
            memory.content,
            memory.source,
            memory.importance,
            memory.metadata
        )
        
        # Get the created memory
        created_memory = await memory_service.get_memory(db, memory_id)
        if not created_memory:
            raise HTTPException(status_code=500, detail="Failed to retrieve created memory")
        
        return created_memory
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating memory: {str(e)}"
        )

@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory(
    memory_id: str = Path(..., description="ID of the memory to retrieve"),
    db: AsyncIOMotorDatabase = Depends(get_async_db)
):
    """
    Get a memory by ID
    """
    try:
        memory = await memory_service.get_memory(db, memory_id)
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        return memory
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving memory: {str(e)}"
        )

@router.post("/search", response_model=MemorySearchResponse)
async def search_memories(
    search: MemorySearch,
    db: AsyncIOMotorDatabase = Depends(get_async_db)
):
    """
    Search memories by semantic similarity
    """
    try:
        memories = await memory_service.search_memories(
            db,
            search.character_id,
            search.query,
            search.limit
        )
        
        return MemorySearchResponse(
            memories=memories,
            query=search.query,
            character_id=search.character_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error searching memories: {str(e)}"
        )

@router.get("/character/{character_id}", response_model=List[MemoryResponse])
async def get_character_memories(
    character_id: str = Path(..., description="ID of the character"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of memories to return"),
    sort_by: str = Query("importance", description="Field to sort by (importance, created_at, last_accessed)"),
    source: Optional[str] = Query(None, description="Filter by source"),
    db: AsyncIOMotorDatabase = Depends(get_async_db)
):
    """
    Get memories for a character
    """
    try:
        memories = await memory_service.get_character_memories(
            db,
            character_id,
            limit,
            sort_by,
            source
        )
        return memories
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving character memories: {str(e)}"
        )

@router.put("/{memory_id}", response_model=MemoryResponse)
async def update_memory(
    memory_update: MemoryUpdate,
    memory_id: str = Path(..., description="ID of the memory to update"),
    db: AsyncIOMotorDatabase = Depends(get_async_db)
):
    """
    Update a memory
    """
    try:
        # Check if memory exists
        existing_memory = await memory_service.get_memory(db, memory_id)
        if not existing_memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        # Update memory
        updates = {k: v for k, v in memory_update.dict().items() if v is not None}
        success = await memory_service.update_memory(db, memory_id, updates)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update memory")
        
        # Get updated memory
        updated_memory = await memory_service.get_memory(db, memory_id)
        return updated_memory
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating memory: {str(e)}"
        )

@router.delete("/{memory_id}", response_model=dict)
async def delete_memory(
    memory_id: str = Path(..., description="ID of the memory to delete"),
    db: AsyncIOMotorDatabase = Depends(get_async_db)
):
    """
    Delete a memory
    """
    try:
        # Check if memory exists
        existing_memory = await memory_service.get_memory(db, memory_id)
        if not existing_memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        # Delete memory
        success = await memory_service.delete_memory(db, memory_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete memory")
        
        return {"message": "Memory deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting memory: {str(e)}"
        ) 