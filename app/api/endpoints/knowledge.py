"""
Knowledge API for managing and retrieving text chunks with vector embeddings
"""
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional, List, Dict, Any

from app.db.mongodb import get_async_db
from app.schemas.knowledge import KnowledgeChunk, KnowledgeQuery
from app.services.knowledge import knowledge_service

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

@router.post("/chunks", response_model=Dict[str, str])
async def create_chunk(
    chunk: KnowledgeChunk,
    db: AsyncIOMotorDatabase = Depends(get_async_db)
):
    """
    Store a knowledge chunk in the database
    """
    try:
        chunk_id = await knowledge_service.store_chunk(db, chunk)
        return {"chunk_id": chunk_id}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error storing knowledge chunk: {str(e)}"
        )

@router.post("/chunks/batch", response_model=Dict[str, List[str]])
async def store_chunks_batch(
    chunks: List[KnowledgeChunk],
    db: AsyncIOMotorDatabase = Depends(get_async_db)
):
    """
    Store multiple knowledge chunks in batch
    """
    try:
        chunk_ids = await knowledge_service.store_chunks_batch(db, chunks)
        return {"chunk_ids": chunk_ids}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error storing knowledge chunks: {str(e)}"
        )

@router.post("/query", response_model=List[KnowledgeChunk])
async def query_knowledge(
    query: KnowledgeQuery,
    db: AsyncIOMotorDatabase = Depends(get_async_db)
):
    """
    Query knowledge chunks by semantic similarity
    """
    try:
        results = await knowledge_service.retrieve_similar(db, query)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error querying knowledge: {str(e)}"
        )

@router.post("/search", response_model=List[Dict[str, Any]])
async def search_knowledge(
    request: dict,
    db: AsyncIOMotorDatabase = Depends(get_async_db)
):
    """
    Search knowledge chunks by semantic similarity (simplified interface)
    """
    try:
        # Convert the simplified request to KnowledgeQuery
        query = KnowledgeQuery(
            query=request.get("query", ""),
            top_k=request.get("top_k", 3),
            filter_metadata=request.get("filter_metadata", None)
        )
        
        # Get results
        results = await knowledge_service.retrieve_similar(db, query)
        
        # Convert to simplified response format
        simplified_results = []
        for chunk in results:
            simplified_results.append({
                "id": chunk.id,
                "content": chunk.content,
                "score": chunk.metadata.get("similarity_score", 0),
                "metadata": chunk.metadata
            })
        
        return simplified_results
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error searching knowledge: {str(e)}"
        )

@router.get("/chunks/{chunk_id}", response_model=KnowledgeChunk)
async def get_chunk(
    chunk_id: str = Path(...),
    db: AsyncIOMotorDatabase = Depends(get_async_db)
):
    """
    Get a specific knowledge chunk by ID
    """
    try:
        chunk = await knowledge_service.get_chunk(db, chunk_id)
        if not chunk:
            raise HTTPException(
                status_code=404,
                detail=f"Knowledge chunk with ID {chunk_id} not found"
            )
        return chunk
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving knowledge chunk: {str(e)}"
        )

@router.put("/chunks/{chunk_id}", response_model=Dict[str, bool])
async def update_chunk(
    chunk: KnowledgeChunk,
    chunk_id: str = Path(...),
    db: AsyncIOMotorDatabase = Depends(get_async_db)
):
    """
    Update a knowledge chunk
    """
    try:
        # Ensure chunk ID matches path parameter
        if chunk.id != chunk_id:
            raise HTTPException(
                status_code=400,
                detail="Chunk ID in body does not match path parameter"
            )
        
        success = await knowledge_service.update_chunk(db, chunk)
        if not success:
            raise HTTPException(status_code=404, detail="Knowledge chunk not found")
        
        return {"success": True}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating knowledge chunk: {str(e)}"
        )

@router.delete("/chunks/{chunk_id}", response_model=Dict[str, bool])
async def delete_chunk(
    chunk_id: str = Path(...),
    db: AsyncIOMotorDatabase = Depends(get_async_db)
):
    """
    Delete a knowledge chunk
    """
    try:
        success = await knowledge_service.delete_chunk(db, chunk_id)
        if not success:
            raise HTTPException(status_code=404, detail="Knowledge chunk not found")
        
        return {"success": True}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting knowledge chunk: {str(e)}"
        )

@router.post("/text-to-chunks", response_model=Dict[str, List[str]])
async def text_to_chunks(
    text: str,
    source: str,
    metadata: Optional[Dict[str, Any]] = None,
    chunk_size: int = Query(500, ge=100, le=2000),
    chunk_overlap: int = Query(50, ge=0, le=500),
    db: AsyncIOMotorDatabase = Depends(get_async_db)
):
    """
    Convert a text into knowledge chunks
    """
    try:
        # Simple chunking by size
        chunks = []
        for i in range(0, len(text), chunk_size - chunk_overlap):
            # Extract chunk text
            chunk_text = text[i:i + chunk_size]
            
            # If this isn't the first chunk and we have overlap, adjust start
            if i > 0 and chunk_overlap > 0:
                chunk_text = text[i - chunk_overlap:i + chunk_size - chunk_overlap]
            
            # Create chunk object
            chunk = KnowledgeChunk(
                source=source,
                content=chunk_text,
                metadata=metadata or {}
            )
            chunks.append(chunk)
        
        # Store chunks
        chunk_ids = await knowledge_service.store_chunks_batch(db, chunks)
        
        return {"chunk_ids": chunk_ids}
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing text to chunks: {str(e)}"
        ) 