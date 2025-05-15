"""
Embedding Service using Hugging Face Transformers for vector embeddings
"""
import os
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
import numpy as np
from sentence_transformers import SentenceTransformer

load_dotenv()

class EmbeddingService:
    """Service for generating vector embeddings using Hugging Face models"""
    
    def __init__(self, model_name: Optional[str] = None):
        """Initialize the embedding service with a model name"""
        self.model_name = model_name or "all-MiniLM-L6-v2"  # Default to a lightweight model
        # Load the model
        try:
            self.model = SentenceTransformer(self.model_name)
            print(f"Loaded embedding model: {self.model_name}")
        except Exception as e:
            print(f"Error loading embedding model: {str(e)}")
            self.model = None
        
    async def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding vector for a text
        
        Args:
            text: The text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        try:
            if not self.model:
                raise ValueError("Embedding model not loaded")
                
            # Generate embedding
            embedding = self.model.encode(text)
            return embedding.tolist()
        
        except Exception as e:
            print(f"Error generating embedding: {str(e)}")
            # Return zero vector as fallback
            return [0.0] * 384  # Common embedding dimension for all-MiniLM-L6-v2
    
    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for multiple texts in batch
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            if not self.model:
                raise ValueError("Embedding model not loaded")
                
            # Generate embeddings in batch
            embeddings = self.model.encode(texts)
            return embeddings.tolist()
        
        except Exception as e:
            print(f"Error generating batch embeddings: {str(e)}")
            # Return zero vectors as fallback
            return [[0.0] * 384 for _ in range(len(texts))]
    
    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity score (0-1)
        """
        # Convert to numpy arrays for efficient calculation
        vec1_array = np.array(vec1)
        vec2_array = np.array(vec2)
        
        # Compute cosine similarity
        dot_product = np.dot(vec1_array, vec2_array)
        norm_vec1 = np.linalg.norm(vec1_array)
        norm_vec2 = np.linalg.norm(vec2_array)
        
        # Avoid division by zero
        if norm_vec1 == 0 or norm_vec2 == 0:
            return 0.0
            
        return dot_product / (norm_vec1 * norm_vec2)

# Create a singleton instance
embedding_service = EmbeddingService() 