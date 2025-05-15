"""
Script to create MongoDB vector search index for memory embeddings
"""
import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "hero_agent")
MEMORY_EMBEDDINGS_COLLECTION = "memory_embeddings"

async def create_vector_index():
    """Create vector search index for memory embeddings"""
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DB_NAME]
    
    print(f"Connected to MongoDB at {MONGODB_URI}")
    print(f"Creating vector search index in database: {DB_NAME}")
    
    # First, create the collection if it doesn't exist
    try:
        # Insert a dummy document to create the collection
        await db[MEMORY_EMBEDDINGS_COLLECTION].insert_one({
            "dummy": True,
            "embedding": [0.1] * 384,  # Dummy embedding vector with correct dimensions
            "character_id": "system",
            "memory_id": "dummy"
        })
        print(f"Created collection '{MEMORY_EMBEDDINGS_COLLECTION}'")
        
        # Remove the dummy document
        await db[MEMORY_EMBEDDINGS_COLLECTION].delete_one({"dummy": True})
        print("Removed dummy document")
    except Exception as e:
        print(f"Note: {str(e)}")
    
    # First, drop existing index if it exists
    try:
        await db.command({
            "dropSearchIndexes": MEMORY_EMBEDDINGS_COLLECTION,
            "name": "memory_embeddings_index"
        })
        print("Dropped existing vector search index")
    except Exception as e:
        print(f"No existing index to drop: {str(e)}")
    
    # Define the updated index with proper configuration
    index_definition = {
        "name": "memory_embeddings_index",
        "definition": {
            "mappings": {
                "dynamic": True,
                "fields": {
                    "embedding": {
                        "type": "knnVector",
                        "dimensions": 384,  # all-MiniLM-L6-v2 embedding dimensions
                        "similarity": "cosine"
                    },
                    "character_id": {
                        "type": "string"
                    },
                    "memory_id": {
                        "type": "string"
                    }
                }
            }
        }
    }
    
    try:
        # Create the index
        await db.command({
            "createSearchIndexes": MEMORY_EMBEDDINGS_COLLECTION,
            "indexes": [index_definition]
        })
        
        print(f"Successfully created vector search index 'memory_embeddings_index'")
        
        # Also create a text index on the memory collection for better regex fallback
        await db["character_memories"].create_index([("content", "text")])
        print("Created text index on character_memories.content")
        
    except Exception as e:
        print(f"Error creating vector search index: {str(e)}")
    finally:
        # Close MongoDB connection
        client.close()

if __name__ == "__main__":
    asyncio.run(create_vector_index()) 