"""
Script to rebuild all memory embeddings with the correct dimensions
"""
import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.memory.service import memory_service
from app.services.embedding import embedding_service

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "hero_agent")

async def rebuild_all_embeddings():
    """Rebuild all memory embeddings with the correct dimensions"""
    print("Rebuilding all memory embeddings...")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DB_NAME]
    
    print(f"Connected to MongoDB at {MONGODB_URI}")
    
    try:
        # Get all memories
        collection = db[memory_service.memory_collection]
        cursor = collection.find({})
        memories = await cursor.to_list(length=1000)
        
        print(f"Found {len(memories)} memories to rebuild embeddings for")
        
        # Delete all existing embeddings
        embeddings_collection = db[memory_service.embeddings_collection]
        delete_result = await embeddings_collection.delete_many({})
        print(f"Deleted {delete_result.deleted_count} existing embeddings")
        
        # Rebuild embeddings
        count = 0
        for memory in memories:
            memory_id = str(memory["_id"])
            character_id = memory.get("character_id", "unknown")
            content = memory.get("content", "")
            
            # Generate new embedding
            embedding = await memory_service.create_embedding(content)
            
            # Store new embedding
            embedding_doc = {
                "memory_id": memory_id,
                "character_id": character_id,
                "embedding": embedding,
                "created_at": memory.get("created_at")
            }
            
            await embeddings_collection.insert_one(embedding_doc)
            count += 1
            
            if count % 10 == 0:
                print(f"Rebuilt {count}/{len(memories)} embeddings")
        
        print(f"Successfully rebuilt {count} embeddings")
        
        # Print sample embedding dimensions
        sample = await embeddings_collection.find_one()
        if sample and "embedding" in sample:
            print(f"Sample embedding dimensions: {len(sample['embedding'])}")
            
    except Exception as e:
        print(f"Error rebuilding embeddings: {str(e)}")
    finally:
        # Close MongoDB connection
        client.close()

if __name__ == "__main__":
    asyncio.run(rebuild_all_embeddings()) 