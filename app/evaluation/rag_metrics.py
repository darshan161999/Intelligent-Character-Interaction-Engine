"""
RAG Evaluation Metrics for Hero Agent

This module provides functions to evaluate the performance of the RAG system
by measuring how effectively retrieved context is used in generating responses.
"""
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np
import datetime
from sklearn.metrics.pairwise import cosine_similarity
from bson.objectid import ObjectId
import logging

# Import for embeddings
from app.services.embeddings import get_embedding

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGEvaluator:
    """Evaluator for RAG metrics"""
    
    def __init__(self, db=None):
        """Initialize the evaluator"""
        self.db = db
        self.evaluation_results = []
    
    async def contextual_precision(
        self, 
        retrieved_chunks: List[Dict[str, Any]], 
        query: str,
        threshold: float = 0.7
    ) -> float:
        """
        Measures whether retrieved context document chunks that are relevant 
        to the given input query are ranked higher than irrelevant ones
        
        Args:
            retrieved_chunks: List of retrieved knowledge chunks
            query: The user's input query
            threshold: Similarity threshold for relevance
            
        Returns:
            Precision score between 0 and 1
        """
        if not retrieved_chunks:
            return 0.0
        
        # Get embedding for the query
        query_embedding = await get_embedding(query)
        
        # Calculate relevance scores for each chunk
        relevant_chunks = 0
        for chunk in retrieved_chunks:
            # Get chunk content
            content = chunk.get("content", "")
            
            # If chunk has embedding, use it; otherwise get new embedding
            if "embedding" in chunk and chunk["embedding"]:
                chunk_embedding = chunk["embedding"]
            else:
                chunk_embedding = await get_embedding(content)
            
            # Calculate similarity
            similarity = cosine_similarity(
                [query_embedding], 
                [chunk_embedding]
            )[0][0]
            
            # Count as relevant if above threshold
            if similarity >= threshold:
                relevant_chunks += 1
        
        # Calculate precision
        precision = relevant_chunks / len(retrieved_chunks) if retrieved_chunks else 0
        return precision
    
    async def contextual_recall(
        self,
        retrieved_chunks: List[Dict[str, Any]],
        expected_response: str,
        threshold: float = 0.7
    ) -> float:
        """
        Measures the extent to which the retrieved context document chunks
        align with the expected response answer (ground truth reference)
        
        Args:
            retrieved_chunks: List of retrieved knowledge chunks
            expected_response: The expected/ground truth response
            threshold: Similarity threshold for relevance
            
        Returns:
            Recall score between 0 and 1
        """
        if not retrieved_chunks or not expected_response:
            return 0.0
        
        # Get embedding for the expected response
        response_embedding = await get_embedding(expected_response)
        
        # Calculate relevance scores for each chunk to the expected response
        relevant_to_response = 0
        for chunk in retrieved_chunks:
            # Get chunk content
            content = chunk.get("content", "")
            
            # If chunk has embedding, use it; otherwise get new embedding
            if "embedding" in chunk and chunk["embedding"]:
                chunk_embedding = chunk["embedding"]
            else:
                chunk_embedding = await get_embedding(content)
            
            # Calculate similarity to expected response
            similarity = cosine_similarity(
                [response_embedding], 
                [chunk_embedding]
            )[0][0]
            
            # Count as relevant if above threshold
            if similarity >= threshold:
                relevant_to_response += 1
        
        # For recall, we need to know how many chunks would be needed for a complete answer
        # This is difficult to determine automatically, so we use a simplified approach:
        # We assume that at least one chunk should be highly relevant to the expected response
        
        # Simple recall calculation (did we retrieve at least one relevant chunk?)
        recall = min(1.0, relevant_to_response)
        
        return recall
    
    async def contextual_relevancy(
        self,
        retrieved_chunks: List[Dict[str, Any]],
        query: str,
        generated_response: str,
        threshold: float = 0.7
    ) -> float:
        """
        Measures the relevancy of the information in the retrieved context
        document chunks to the given input query
        
        Args:
            retrieved_chunks: List of retrieved knowledge chunks
            query: The user's input query
            generated_response: The response generated by the system
            threshold: Similarity threshold for relevance
            
        Returns:
            Relevancy score between 0 and 1
        """
        if not retrieved_chunks:
            return 0.0
        
        # Get embeddings
        query_embedding = await get_embedding(query)
        response_embedding = await get_embedding(generated_response)
        
        # Calculate average relevance of chunks to both query and response
        relevance_scores = []
        for chunk in retrieved_chunks:
            # Get chunk content
            content = chunk.get("content", "")
            
            # If chunk has embedding, use it; otherwise get new embedding
            if "embedding" in chunk and chunk["embedding"]:
                chunk_embedding = chunk["embedding"]
            else:
                chunk_embedding = await get_embedding(content)
            
            # Calculate similarity to query and response
            query_similarity = cosine_similarity(
                [query_embedding], 
                [chunk_embedding]
            )[0][0]
            
            response_similarity = cosine_similarity(
                [response_embedding], 
                [chunk_embedding]
            )[0][0]
            
            # Combined relevance score (geometric mean)
            combined_relevance = np.sqrt(query_similarity * response_similarity)
            relevance_scores.append(combined_relevance)
        
        # Calculate average relevance
        avg_relevance = np.mean(relevance_scores) if relevance_scores else 0.0
        return float(avg_relevance)
    
    async def evaluate_response(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        generated_response: str,
        expected_response: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a single response using all metrics
        
        Args:
            query: The user's input query
            retrieved_chunks: List of retrieved knowledge chunks
            generated_response: The response generated by the system
            expected_response: Optional expected/ground truth response
            conversation_id: Optional conversation ID
            
        Returns:
            Dictionary with evaluation metrics
        """
        logger.info(f"Evaluating response for query: {query[:50]}...")
        
        # Calculate metrics
        precision = await self.contextual_precision(retrieved_chunks, query)
        logger.info(f"Calculated precision: {precision:.2f}")
        
        # Only calculate recall if expected response is provided
        recall = 0.0
        if expected_response:
            recall = await self.contextual_recall(retrieved_chunks, expected_response)
            logger.info(f"Calculated recall: {recall:.2f}")
            
        relevancy = await self.contextual_relevancy(retrieved_chunks, query, generated_response)
        logger.info(f"Calculated relevancy: {relevancy:.2f}")
        
        # Create evaluation result
        result = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "query": query,
            "generated_response": generated_response,
            "expected_response": expected_response,
            "retrieved_chunks_count": len(retrieved_chunks),
            "retrieved_chunk_ids": [str(chunk.get("id", "unknown")) for chunk in retrieved_chunks],
            "metrics": {
                "contextual_precision": float(precision),
                "contextual_recall": float(recall) if expected_response else None,
                "contextual_relevancy": float(relevancy),
                "combined_score": float(np.mean([precision, relevancy, recall if expected_response else 0]))
            },
            "conversation_id": str(conversation_id) if conversation_id else None
        }
        
        # Store result
        self.evaluation_results.append(result)
        
        # If DB is provided, store in database
        if self.db is not None:
            try:
                logger.info("Storing evaluation result in database")
                # Create a copy of the result for MongoDB with proper ObjectId
                db_result = result.copy()
                if conversation_id:
                    try:
                        db_result["conversation_id"] = ObjectId(conversation_id) if isinstance(conversation_id, str) else conversation_id
                    except:
                        # If conversion fails, keep as string
                        pass
                
                await self.db["rag_evaluations"].insert_one(db_result)
            except Exception as e:
                logger.error(f"Error storing evaluation result: {str(e)}")
        
        return result
    
    async def get_evaluation_summary(
        self, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get summary statistics for recent evaluations
        
        Args:
            limit: Maximum number of recent evaluations to include
            
        Returns:
            Dictionary with summary statistics
        """
        # Get most recent results
        recent_results = self.evaluation_results[-limit:] if self.evaluation_results else []
        
        if not recent_results:
            return {
                "count": 0,
                "metrics": {
                    "avg_contextual_precision": 0.0,
                    "avg_contextual_recall": 0.0,
                    "avg_contextual_relevancy": 0.0,
                    "avg_combined_score": 0.0
                }
            }
        
        # Calculate averages
        precision_values = [float(r["metrics"]["contextual_precision"]) for r in recent_results]
        avg_precision = float(np.mean(precision_values)) if precision_values else 0.0
        
        # Only include recall values that are not None
        recall_values = [float(r["metrics"]["contextual_recall"]) for r in recent_results 
                        if r["metrics"]["contextual_recall"] is not None]
        avg_recall = float(np.mean(recall_values)) if recall_values else 0.0
        
        relevancy_values = [float(r["metrics"]["contextual_relevancy"]) for r in recent_results]
        avg_relevancy = float(np.mean(relevancy_values)) if relevancy_values else 0.0
        
        combined_values = [float(r["metrics"]["combined_score"]) for r in recent_results]
        avg_combined = float(np.mean(combined_values)) if combined_values else 0.0
        
        return {
            "count": len(recent_results),
            "metrics": {
                "avg_contextual_precision": avg_precision,
                "avg_contextual_recall": avg_recall,
                "avg_contextual_relevancy": avg_relevancy,
                "avg_combined_score": avg_combined
            }
        }

# Create singleton instance
rag_evaluator = RAGEvaluator() 