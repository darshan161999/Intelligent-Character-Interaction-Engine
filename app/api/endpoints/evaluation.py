"""
Evaluation API endpoints for RAG metrics
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import traceback
import logging

from app.db.mongodb import get_async_db
from app.evaluation.rag_metrics import rag_evaluator
from app.schemas.dialogue import DialogueRequest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/evaluation", tags=["evaluation"])

class RAGEvaluationRequest(BaseModel):
    """Request model for RAG evaluation"""
    query: str
    retrieved_chunks: List[Dict[str, Any]]
    generated_response: str
    expected_response: Optional[str] = None
    conversation_id: Optional[str] = None

@router.post("/rag-metrics")
async def evaluate_rag(
    request: RAGEvaluationRequest,
    db: AsyncIOMotorDatabase = Depends(get_async_db)
):
    """
    Evaluate RAG metrics for a response
    
    Args:
        request: RAG evaluation request containing query, chunks, and response
        
    Returns:
        Evaluation metrics
    """
    try:
        logger.info(f"Processing RAG evaluation for query: {request.query[:50]}...")
        logger.info(f"Number of chunks: {len(request.retrieved_chunks)}")
        
        # Set database for evaluator if not already set
        if rag_evaluator.db is None:
            rag_evaluator.db = db
            
        # Evaluate response
        result = await rag_evaluator.evaluate_response(
            query=request.query,
            retrieved_chunks=request.retrieved_chunks,
            generated_response=request.generated_response,
            expected_response=request.expected_response,
            conversation_id=request.conversation_id
        )
        
        logger.info("RAG evaluation completed successfully")
        return result
    except Exception as e:
        error_detail = f"Error evaluating RAG metrics: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_detail)
        raise HTTPException(
            status_code=500,
            detail=error_detail
        )

@router.get("/rag-summary")
async def get_rag_summary(
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncIOMotorDatabase = Depends(get_async_db)
):
    """
    Get summary of RAG evaluation metrics
    
    Args:
        limit: Maximum number of recent evaluations to include
        
    Returns:
        Summary statistics
    """
    try:
        logger.info(f"Getting RAG evaluation summary with limit: {limit}")
        
        # Set database for evaluator if not already set
        if rag_evaluator.db is None:
            rag_evaluator.db = db
            
        # Get summary
        summary = await rag_evaluator.get_evaluation_summary(limit=limit)
        
        logger.info("RAG summary retrieved successfully")
        return summary
    except Exception as e:
        error_detail = f"Error getting RAG summary: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_detail)
        raise HTTPException(
            status_code=500,
            detail=error_detail
        ) 