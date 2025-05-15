"""
Knowledge Service for managing and retrieving information from the vector database
"""
import os
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import MongoClient
from app.schemas.knowledge import KnowledgeChunk, KnowledgeQuery
from app.services.embedding import embedding_service
from app.db.mongodb import get_sync_db, ensure_vector_index
import numpy as np
from bson import ObjectId

class KnowledgeService:
    """Service for knowledge retrieval and management"""
    
    def __init__(self, collection_name: str = "knowledge_chunks"):
        """Initialize the knowledge service"""
        self.collection_name = collection_name
        # Ensure the vector index exists
        ensure_vector_index(collection_name)
    
    async def store_chunk(self, db: AsyncIOMotorDatabase, chunk: KnowledgeChunk) -> str:
        """
        Store a knowledge chunk in the database
        
        Args:
            db: AsyncIOMotorDatabase instance
            chunk: The knowledge chunk to store
            
        Returns:
            The ID of the stored chunk
        """
        # If no embedding exists, generate one
        if not chunk.vector_embedding:
            chunk.vector_embedding = await embedding_service.get_embedding(chunk.content)
        
        # Insert the chunk
        collection = db[self.collection_name]
        result = await collection.insert_one(chunk.dict())
        return str(result.inserted_id)
    
    async def store_chunks_batch(self, db: AsyncIOMotorDatabase, chunks: List[KnowledgeChunk]) -> List[str]:
        """
        Store multiple knowledge chunks in batch
        
        Args:
            db: AsyncIOMotorDatabase instance
            chunks: List of knowledge chunks to store
            
        Returns:
            List of IDs of stored chunks
        """
        # Process chunks that don't have embeddings
        chunks_without_embedding = [c for c in chunks if not c.vector_embedding]
        if chunks_without_embedding:
            texts = [c.content for c in chunks_without_embedding]
            embeddings = await embedding_service.get_embeddings_batch(texts)
            
            # Assign embeddings to chunks
            for chunk, embedding in zip(chunks_without_embedding, embeddings):
                chunk.vector_embedding = embedding
        
        # Insert all chunks
        collection = db[self.collection_name]
        result = await collection.insert_many([c.dict() for c in chunks])
        return [str(id) for id in result.inserted_ids]
    
    async def retrieve_similar(
        self, 
        db: AsyncIOMotorDatabase, 
        query: KnowledgeQuery
    ) -> List[KnowledgeChunk]:
        """
        Retrieve knowledge chunks similar to the query
        
        Args:
            db: AsyncIOMotorDatabase instance
            query: The query to find similar chunks for
            
        Returns:
            List of knowledge chunks with similarity scores
        """
        print(f"Retrieving similar chunks for query: '{query.query}'")
        print(f"Filter metadata: {query.filter_metadata}")
        
        # Get embedding for query
        query_embedding = await embedding_service.get_embedding(query.query)
        print(f"Generated embedding with {len(query_embedding)} dimensions")
        
        # Try a basic query first to check if the collection has data
        collection = db[self.collection_name]
        count = await collection.count_documents({})
        print(f"Total documents in collection: {count}")
        
        # Use simple text search instead of vector search
        print("Using simple text search")
        
        # Prepare filter
        filter_query = {}
        
        # Add metadata filter if specified
        if query.filter_metadata:
            for key, value in query.filter_metadata.items():
                filter_query[f"metadata.{key}"] = value
        
        print(f"Filter query: {filter_query}")
        
        # Execute simple text search
        try:
            # Get all chunks matching the filter
            results = await collection.find(filter_query).to_list(length=100)
            print(f"Found {len(results)} chunks matching filter")
            
            # Convert results to KnowledgeChunk objects
            chunks = []
            for result in results:
                # Convert MongoDB _id to string
                result["id"] = str(result.pop("_id"))
                chunks.append(KnowledgeChunk(**result))
            
            # Calculate similarity scores manually
            for chunk in chunks:
                if chunk.vector_embedding:
                    similarity = embedding_service.cosine_similarity(
                        query_embedding, 
                        chunk.vector_embedding
                    )
                    if "metadata" not in chunk.dict():
                        chunk.metadata = {}
                    chunk.metadata["similarity_score"] = similarity
            
            # Sort by similarity score (highest first)
            chunks.sort(
                key=lambda c: c.metadata.get("similarity_score", 0),
                reverse=True
            )
            
            # Limit to top_k results
            chunks = chunks[:query.top_k]
            
            print(f"Returning {len(chunks)} chunks after sorting by similarity")
            return chunks
            
        except Exception as e:
            print(f"Error in text search: {str(e)}")
            return []
    
    async def delete_chunk(self, db: AsyncIOMotorDatabase, chunk_id: str) -> bool:
        """
        Delete a knowledge chunk from the database
        
        Args:
            db: AsyncIOMotorDatabase instance
            chunk_id: The ID of the chunk to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        collection = db[self.collection_name]
        result = await collection.delete_one({"_id": chunk_id})
        return result.deleted_count > 0
    
    async def update_chunk(self, db: AsyncIOMotorDatabase, chunk: KnowledgeChunk) -> bool:
        """
        Update a knowledge chunk in the database
        
        Args:
            db: AsyncIOMotorDatabase instance
            chunk: The knowledge chunk to update
            
        Returns:
            True if update was successful, False otherwise
        """
        # If content was updated, regenerate embedding
        collection = db[self.collection_name]
        chunk_dict = chunk.dict()
        chunk_id = chunk_dict.pop("id")
        
        result = await collection.update_one(
            {"_id": chunk_id},
            {"$set": chunk_dict}
        )
        return result.modified_count > 0
    
    async def get_chunk(self, db: AsyncIOMotorDatabase, chunk_id: str) -> Optional[KnowledgeChunk]:
        """
        Get a knowledge chunk by ID
        
        Args:
            db: AsyncIOMotorDatabase instance
            chunk_id: The ID of the chunk to retrieve
            
        Returns:
            The knowledge chunk if found, None otherwise
        """
        try:
            # Try to convert string ID to ObjectId
            obj_id = chunk_id
            if not isinstance(chunk_id, ObjectId):
                try:
                    obj_id = ObjectId(chunk_id)
                except:
                    # If conversion fails, keep original ID
                    pass
            
            collection = db[self.collection_name]
            result = await collection.find_one({"_id": obj_id})
            
            if result:
                # Convert MongoDB _id to string
                result["id"] = str(result.pop("_id"))
                return KnowledgeChunk(**result)
            
            return None
            
        except Exception as e:
            print(f"Error retrieving knowledge chunk: {str(e)}")
            return None

# Create a singleton instance
knowledge_service = KnowledgeService() 