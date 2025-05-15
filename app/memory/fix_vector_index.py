"""
Script to fix MongoDB Atlas vector search index
"""
import os
import asyncio
import json
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "hero_agent")
MEMORY_EMBEDDINGS_COLLECTION = "memory_embeddings"

async def fix_vector_index():
    """Fix vector search index for memory embeddings"""
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DB_NAME]
    
    print(f"Connected to MongoDB at {MONGODB_URI}")
    print(f"Fixing vector search index in database: {DB_NAME}")
    
    try:
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
        
        # For MongoDB Atlas, we need to use the admin command
        print("\nCreating vector search index...")
        
        # Define the index definition
        index_definition = {
            "mappings": {
                "dynamic": True,
                "fields": {
                    "embedding": {
                        "dimensions": 384,
                        "similarity": "cosine",
                        "type": "knnVector"
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
        
        # Create the index using the admin command
        try:
            result = await db.command({
                "createSearchIndex": MEMORY_EMBEDDINGS_COLLECTION,
                "name": "memory_embeddings_index",
                "definition": index_definition
            })
            print(f"Successfully created vector search index: {result}")
        except Exception as e:
            if "already exists" in str(e):
                print("Index already exists, attempting to drop and recreate...")
                try:
                    # Drop the existing index
                    drop_result = await db.command({
                        "dropSearchIndex": MEMORY_EMBEDDINGS_COLLECTION,
                        "name": "memory_embeddings_index"
                    })
                    print(f"Successfully dropped index: {drop_result}")
                    
                    # Recreate the index
                    create_result = await db.command({
                        "createSearchIndex": MEMORY_EMBEDDINGS_COLLECTION,
                        "name": "memory_embeddings_index",
                        "definition": index_definition
                    })
                    print(f"Successfully recreated vector search index: {create_result}")
                except Exception as drop_error:
                    print(f"Error dropping/recreating index: {str(drop_error)}")
            else:
                print(f"Error creating vector search index: {str(e)}")
        
        # Create a text index on the memory collection for better regex fallback
        print("\nCreating text index on character_memories.content...")
        await db["character_memories"].create_index([("content", "text")])
        print("Successfully created text index")
        
        # Print collection stats to verify
        stats = await db.command("collStats", MEMORY_EMBEDDINGS_COLLECTION)
        print(f"\nCollection stats: {stats.get('ns')}")
        print(f"Document count: {stats.get('count')}")
        print(f"Size: {stats.get('size')} bytes")
        
        # Print some sample documents
        print("\nSample documents:")
        cursor = db[MEMORY_EMBEDDINGS_COLLECTION].find().limit(2)
        async for doc in cursor:
            doc_copy = doc.copy()
            # Truncate embedding for display
            if "embedding" in doc_copy:
                doc_copy["embedding"] = f"[{doc_copy['embedding'][0]:.4f}, {doc_copy['embedding'][1]:.4f}, ... {len(doc_copy['embedding'])} values]"
            print(json.dumps(doc_copy, default=str, indent=2))
        
    except Exception as e:
        print(f"Error fixing vector search index: {str(e)}")
    finally:
        # Close MongoDB connection
        client.close()

if __name__ == "__main__":
    asyncio.run(fix_vector_index()) 