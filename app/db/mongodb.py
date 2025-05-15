"""
MongoDB connection module
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://nemaded:34VjOgwdQPPgW45M@cluster0.urtxinp.mongodb.net/")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "hero_agent")

# Async client for FastAPI
async def get_async_db():
    """
    Get async MongoDB client connection
    """
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[MONGODB_DB_NAME]
    try:
        yield db
    finally:
        client.close()

# Sync client for utility scripts
def get_sync_db():
    """
    Get synchronous MongoDB client connection
    """
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB_NAME]
    return db

# Create vector index for knowledge retrieval
def ensure_vector_index(collection_name="knowledge_chunks"):
    """
    Ensure vector search index exists
    """
    db = get_sync_db()
    collection = db[collection_name]
    
    # Check if index already exists
    existing_indexes = collection.list_indexes()
    index_exists = False
    for index in existing_indexes:
        if index.get('name') == 'vector_index':
            index_exists = True
            break
    
    if not index_exists:
        # Create vector index
        collection.create_index(
            [("vector_embedding", "2dsphere")],
            name="vector_index"
        )
        print(f"Created vector index on {collection_name}")
    
    return True 