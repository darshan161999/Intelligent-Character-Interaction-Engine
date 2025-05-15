"""
Memory Service for managing character long-term memory
"""
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from motor.motor_asyncio import AsyncIOMotorDatabase
from groq import AsyncGroq
from dotenv import load_dotenv
from bson.objectid import ObjectId

from app.services.embedding import embedding_service

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MEMORY_COLLECTION = "character_memories"
MEMORY_EMBEDDINGS_COLLECTION = "memory_embeddings"

class MemoryService:
    """Service for managing character long-term memory"""
    
    def __init__(
        self,
        memory_collection: str = MEMORY_COLLECTION,
        embeddings_collection: str = MEMORY_EMBEDDINGS_COLLECTION,
        api_key: Optional[str] = None
    ):
        """Initialize the memory service"""
        self.memory_collection = memory_collection
        self.embeddings_collection = embeddings_collection
        self.api_key = api_key or GROQ_API_KEY
        print("Using MongoDB Atlas for memory storage")
        
    async def create_embedding(self, text: str) -> List[float]:
        """
        Create an embedding for text using embedding service
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        # Use the embedding service to generate embeddings
        try:
            embedding = await embedding_service.get_embedding(text)
            return embedding
        except Exception as e:
            print(f"Error generating embedding: {str(e)}")
            # Re-raise the exception instead of returning a dummy vector
            raise
        
    async def create_memory(
        self,
        db: AsyncIOMotorDatabase,
        character_id: str,
        content: str,
        source: str = "conversation",
        importance: int = 5,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new memory for a character
        
        Args:
            db: AsyncIOMotorDatabase instance
            character_id: ID of the character
            content: Content of the memory
            source: Source of the memory (conversation, wiki, etc.)
            importance: Importance score (1-10)
            metadata: Optional metadata for the memory
            
        Returns:
            ID of the created memory
        """
        # Create memory document
        memory = {
            "character_id": character_id,
            "content": content,
            "source": source,
            "importance": importance,
            "metadata": metadata or {},
            "created_at": datetime.utcnow(),
            "last_accessed": datetime.utcnow(),
            "access_count": 0
        }
        
        # Insert memory
        collection = db[self.memory_collection]
        result = await collection.insert_one(memory)
        memory_id = str(result.inserted_id)
        
        # Generate embedding for memory
        embedding = await self.create_embedding(content)
        
        # Store embedding
        embedding_doc = {
            "memory_id": memory_id,
            "character_id": character_id,
            "embedding": embedding,
            "created_at": datetime.utcnow()
        }
        
        embeddings_collection = db[self.embeddings_collection]
        await embeddings_collection.insert_one(embedding_doc)
        
        return memory_id
    
    async def get_memory(
        self,
        db: AsyncIOMotorDatabase,
        memory_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a memory by ID
        
        Args:
            db: AsyncIOMotorDatabase instance
            memory_id: ID of the memory
            
        Returns:
            The memory or None if not found
        """
        collection = db[self.memory_collection]
        
        try:
            # Try to parse as ObjectId first
            try:
                object_id = ObjectId(memory_id)
                result = await collection.find_one({"_id": object_id})
            except:
                # If not a valid ObjectId, try as string
                result = await collection.find_one({"_id": memory_id})
        
            if result:
                # Update access stats
                await collection.update_one(
                    {"_id": result["_id"]},
                    {
                        "$set": {"last_accessed": datetime.utcnow()},
                        "$inc": {"access_count": 1}
                    }
                )
                
                result["id"] = str(result.pop("_id"))
                return result
        except Exception as e:
            print(f"Error retrieving memory {memory_id}: {str(e)}")
            
        return None
    
    async def search_memories(
        self,
        db: AsyncIOMotorDatabase,
        character_id: str,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search memories by content using vector search, falling back to regex
        
        Args:
            db: AsyncIOMotorDatabase instance
            character_id: ID of the character
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of relevant memories
        """
        try:
            # Generate embedding for the query
            query_embedding = await self.create_embedding(query)
            
            # Debug info
            print(f"Running manual vector search for '{query}' with {len(query_embedding)} dimensions")
            
            try:
                # Try MongoDB Atlas vector search first
                collection = db[self.memory_collection]
                pipeline = [
                    {
                        "$search": {
                            "index": "vector_index",
                            "knnBeta": {
                                "vector": query_embedding,
                                "path": "vector_embedding",
                                "k": limit
                            }
                        }
                    },
                    {
                        "$match": {
                            "character_id": character_id
                        }
                    },
                    {
                        "$limit": limit
                    }
                ]
                
                results = await collection.aggregate(pipeline).to_list(length=limit)
                
                if results:
                    print(f"MongoDB Atlas vector search found {len(results)} results")
                    
                    # Process results
                    for result in results:
                        result["id"] = str(result.pop("_id"))
                        
                        # Calculate similarity score
                        if "vector_embedding" in result:
                            similarity = embedding_service.cosine_similarity(
                                query_embedding, 
                                result["vector_embedding"]
                            )
                            
                            # Add to metadata
                            if "metadata" not in result:
                                result["metadata"] = {}
                            result["metadata"]["similarity_score"] = similarity
                    
                    # Update access stats
                    for memory in results:
                        await collection.update_one(
                            {"_id": memory["id"]},
                            {
                                "$set": {"last_accessed": datetime.utcnow()},
                                "$inc": {"access_count": 1}
                            }
                        )
                    
                    return results
                
                print("MongoDB Atlas vector search returned no results, falling back to manual search")
            except Exception as e:
                print(f"MongoDB Atlas vector search failed: {str(e)}, falling back to manual search")
            
            # Get all embeddings for this character
            embeddings_collection = db[self.embeddings_collection]
            cursor = embeddings_collection.find({"character_id": character_id})
            
            # Calculate similarity manually
            embedding_results = []
            async for doc in cursor:
                if "embedding" in doc and isinstance(doc["embedding"], list):
                    # Calculate cosine similarity
                    similarity = embedding_service.cosine_similarity(query_embedding, doc["embedding"])
                    embedding_results.append({
                        "memory_id": doc["memory_id"],
                        "score": similarity
                    })
            
            # Sort by similarity and take top results
            embedding_results.sort(key=lambda x: x["score"], reverse=True)
            embedding_results = embedding_results[:limit]
            
            # Get full memory documents
            memories = []
            for result in embedding_results:
                memory = await self.get_memory(db, result["memory_id"])
                if memory:
                    # Add similarity score to metadata
                    if "metadata" not in memory:
                        memory["metadata"] = {}
                    memory["metadata"]["similarity_score"] = result["score"]
                    memories.append(memory)
            
            print(f"Manual vector search found {len(memories)} results")
            return memories
            
        except Exception as e:
            print(f"Vector search failed: {str(e)}, falling back to text search")
            
            try:
                # Fall back to text search
                collection = db[self.memory_collection]
                query_regex = {"$regex": query, "$options": "i"}
                cursor = collection.find({
                    "character_id": character_id,
                    "$or": [
                        {"content": query_regex},
                        {"metadata.topic": query_regex},
                        {"metadata.category": query_regex}
                    ]
                }).limit(limit)
                
                results = []
                async for doc in cursor:
                    doc["id"] = str(doc.pop("_id"))
                    results.append(doc)
                
                if results:
                    print(f"Text search found {len(results)} results")
                    return results
                
                # If text search fails too, fall back to most important memories
                return await self.get_character_memories(db, character_id, limit)
            
            except Exception as text_error:
                print(f"Text search failed: {str(text_error)}, falling back to most important memories")
                return await self.get_character_memories(db, character_id, limit)
    
    async def get_character_memories(
        self,
        db: AsyncIOMotorDatabase,
        character_id: str,
        limit: int = 10,
        sort_by: str = "importance",
        source: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get memories for a character
        
        Args:
            db: AsyncIOMotorDatabase instance
            character_id: ID of the character
            limit: Maximum number of results
            sort_by: Field to sort by (importance, created_at, last_accessed)
            source: Optional filter by source
            
        Returns:
            List of memories
        """
        collection = db[self.memory_collection]
        
        # Build query
        query = {"character_id": character_id}
        if source:
            query["source"] = source
        
        # Determine sort order
        sort_order = -1  # Descending
        if sort_by == "created_at":
            sort_field = "created_at"
        elif sort_by == "last_accessed":
            sort_field = "last_accessed"
        else:
            sort_field = "importance"
        
        # Execute query
        cursor = collection.find(query).sort(sort_field, sort_order).limit(limit)
        results = await cursor.to_list(length=limit)
        
        # Process results
        memories = []
        for memory in results:
            memory["id"] = str(memory.pop("_id"))
            memories.append(memory)
        
        return memories
    
    async def update_memory(
        self,
        db: AsyncIOMotorDatabase,
        memory_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update a memory
        
        Args:
            db: AsyncIOMotorDatabase instance
            memory_id: ID of the memory
            updates: Fields to update
            
        Returns:
            True if successful, False otherwise
        """
        collection = db[self.memory_collection]
        
        # Ensure we're not updating restricted fields
        safe_updates = {k: v for k, v in updates.items() 
                       if k not in ["_id", "character_id", "created_at"]}
        
        # Update memory
        result = await collection.update_one(
            {"_id": memory_id},
            {"$set": safe_updates}
        )
        
        # If content was updated, update the embedding
        if "content" in safe_updates:
            memory = await collection.find_one({"_id": memory_id})
            if memory:
                # Generate new embedding
                new_embedding = await self.create_embedding(safe_updates["content"])
                
                # Update embedding
                embeddings_collection = db[self.embeddings_collection]
                await embeddings_collection.update_one(
                    {"memory_id": memory_id},
                    {"$set": {"embedding": new_embedding}}
                )
        
        return result.modified_count > 0
    
    async def delete_memory(
        self,
        db: AsyncIOMotorDatabase,
        memory_id: str
    ) -> bool:
        """
        Delete a memory
        
        Args:
            db: AsyncIOMotorDatabase instance
            memory_id: ID of the memory
            
        Returns:
            True if successful, False otherwise
        """
        # Delete memory
        collection = db[self.memory_collection]
        result = await collection.delete_one({"_id": memory_id})
        
        # Delete embedding
        if result.deleted_count > 0:
            embeddings_collection = db[self.embeddings_collection]
            await embeddings_collection.delete_one({"memory_id": memory_id})
        
        return result.deleted_count > 0

# Create singleton instance
memory_service = MemoryService() 