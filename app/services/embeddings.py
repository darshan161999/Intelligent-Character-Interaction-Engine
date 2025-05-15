"""
Embeddings Service for text vectorization
"""
import os
import numpy as np
import hashlib
from typing import List, Dict, Any, Optional
import httpx
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get API keys from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Default embedding model
DEFAULT_EMBEDDING_MODEL = "text-embedding-ada-002"

# Cache for embeddings to avoid redundant API calls
embedding_cache = {}

def get_deterministic_embedding(text: str, vector_size: int = 1536) -> List[float]:
    """
    Generate a deterministic embedding based on text hash
    This is used as a fallback when API calls fail
    
    Args:
        text: The text to embed
        vector_size: Size of the embedding vector
        
    Returns:
        A deterministic embedding vector
    """
    # Create a hash of the text
    text_hash = hashlib.md5(text.encode()).hexdigest()
    
    # Use the hash to seed numpy's random number generator
    np.random.seed(int(text_hash, 16) % (2**32))
    
    # Generate a deterministic random vector
    embedding = np.random.rand(vector_size)
    
    # Normalize the vector to have unit length
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding = embedding / norm
    
    return embedding.tolist()

async def get_embedding(
    text: str,
    model: str = DEFAULT_EMBEDDING_MODEL,
    use_cache: bool = True,
    use_fallback: bool = True
) -> List[float]:
    """
    Get embedding for a text using OpenAI's embedding API
    
    Args:
        text: The text to embed
        model: The embedding model to use
        use_cache: Whether to use the cache
        use_fallback: Whether to use fallback method if API fails
        
    Returns:
        The embedding vector
    """
    # Check cache first if enabled
    if use_cache and text in embedding_cache:
        logger.debug(f"Using cached embedding for text: {text[:30]}...")
        return embedding_cache[text]
    
    # Prepare text
    text = text.replace("\n", " ")
    
    try:
        # Use OpenAI API for embeddings
        if OPENAI_API_KEY:
            logger.info(f"Getting embedding from OpenAI API for text: {text[:30]}...")
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/embeddings",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {OPENAI_API_KEY}"
                    },
                    json={
                        "input": text,
                        "model": model
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    embedding = result["data"][0]["embedding"]
                    
                    # Cache the result if caching is enabled
                    if use_cache:
                        embedding_cache[text] = embedding
                    
                    return embedding
                else:
                    logger.warning(f"Error getting embedding: {response.status_code} - {response.text}")
                    if use_fallback:
                        logger.info("Using fallback deterministic embedding")
                        embedding = get_deterministic_embedding(text)
                        if use_cache:
                            embedding_cache[text] = embedding
                        return embedding
                    else:
                        raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")
        else:
            logger.warning("OpenAI API key not found")
            if use_fallback:
                logger.info("Using fallback deterministic embedding")
                embedding = get_deterministic_embedding(text)
                if use_cache:
                    embedding_cache[text] = embedding
                return embedding
            else:
                raise Exception("OpenAI API key not found and fallback disabled")
            
    except Exception as e:
        logger.error(f"Error in get_embedding: {str(e)}")
        if use_fallback:
            logger.info("Using fallback deterministic embedding due to error")
            embedding = get_deterministic_embedding(text)
            if use_cache:
                embedding_cache[text] = embedding
            return embedding
        else:
            raise

async def batch_get_embeddings(
    texts: List[str],
    model: str = DEFAULT_EMBEDDING_MODEL,
    use_cache: bool = True,
    use_fallback: bool = True
) -> List[List[float]]:
    """
    Get embeddings for multiple texts
    
    Args:
        texts: List of texts to embed
        model: The embedding model to use
        use_cache: Whether to use the cache
        use_fallback: Whether to use fallback method if API fails
        
    Returns:
        List of embedding vectors
    """
    results = []
    for text in texts:
        embedding = await get_embedding(text, model, use_cache, use_fallback)
        results.append(embedding)
    return results

def cosine_similarity_score(v1: List[float], v2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors
    
    Args:
        v1: First vector
        v2: Second vector
        
    Returns:
        Cosine similarity score
    """
    v1_array = np.array(v1)
    v2_array = np.array(v2)
    
    dot_product = np.dot(v1_array, v2_array)
    norm_v1 = np.linalg.norm(v1_array)
    norm_v2 = np.linalg.norm(v2_array)
    
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    
    return dot_product / (norm_v1 * norm_v2) 