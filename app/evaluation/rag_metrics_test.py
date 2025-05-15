"""
Simple test script for RAG metrics
"""
import asyncio
import logging
from app.evaluation.rag_metrics import RAGEvaluator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_rag_metrics():
    """Test RAG metrics with simple data"""
    logger.info("Starting RAG metrics test")
    
    # Create a new evaluator instance (not using the singleton)
    evaluator = RAGEvaluator()
    
    # Test data
    query = "What is the weather like?"
    retrieved_chunks = [
        {
            "id": "test_chunk_1",
            "content": "The weather is sunny today with a high of 75 degrees."
        }
    ]
    generated_response = "Today is sunny with temperatures reaching 75 degrees."
    
    # Test precision
    logger.info("Testing contextual precision...")
    precision = await evaluator.contextual_precision(retrieved_chunks, query)
    logger.info(f"Precision: {precision}")
    
    # Test relevancy
    logger.info("Testing contextual relevancy...")
    relevancy = await evaluator.contextual_relevancy(retrieved_chunks, query, generated_response)
    logger.info(f"Relevancy: {relevancy}")
    
    # Test full evaluation
    logger.info("Testing full evaluation...")
    result = await evaluator.evaluate_response(
        query=query,
        retrieved_chunks=retrieved_chunks,
        generated_response=generated_response
    )
    
    logger.info(f"Evaluation result: {result}")
    logger.info("RAG metrics test completed")

if __name__ == "__main__":
    asyncio.run(test_rag_metrics()) 