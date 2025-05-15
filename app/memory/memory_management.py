"""
Memory Management Utility for maintenance tasks
"""
import asyncio
import sys
import os
import argparse
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.memory.service import memory_service

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "hero_agent")

async def prune_memories(character_id: Optional[str] = None, days: int = 30, 
                         max_access_count: int = 0, dry_run: bool = True):
    """
    Prune old, rarely accessed memories
    
    Args:
        character_id: Optional character ID to filter by
        days: Remove memories older than this many days
        max_access_count: Only remove memories with access count less than or equal to this
        dry_run: If True, only print what would be deleted without actually deleting
    """
    print(f"{'[DRY RUN] ' if dry_run else ''}Pruning old memories...")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DB_NAME]
    
    # Build query
    query = {}
    if character_id:
        query["character_id"] = character_id
    
    # Add date filter
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    query["created_at"] = {"$lt": cutoff_date}
    
    # Add access count filter
    query["access_count"] = {"$lte": max_access_count}
    
    # Get memories to delete
    collection = db[memory_service.memory_collection]
    cursor = collection.find(query)
    memories = await cursor.to_list(length=1000)
    
    print(f"Found {len(memories)} memories to prune")
    
    if memories:
        for memory in memories[:5]:  # Show sample of memories to be pruned
            print(f"- {memory.get('content', '')[:50]}... (character: {memory.get('character_id')}, "
                  f"created: {memory.get('created_at')}, accesses: {memory.get('access_count', 0)})")
        
        if len(memories) > 5:
            print(f"... and {len(memories) - 5} more")
        
        if not dry_run:
            # Delete memories
            memory_ids = [memory["_id"] for memory in memories]
            
            # Delete from memory collection
            delete_result = await collection.delete_many({"_id": {"$in": memory_ids}})
            print(f"Deleted {delete_result.deleted_count} memories")
            
            # Delete from embeddings collection
            embeddings_collection = db[memory_service.embeddings_collection]
            embed_delete_result = await embeddings_collection.delete_many(
                {"memory_id": {"$in": [str(mid) for mid in memory_ids]}}
            )
            print(f"Deleted {embed_delete_result.deleted_count} memory embeddings")
    
    # Close MongoDB connection
    client.close()

async def rebuild_embeddings(character_id: Optional[str] = None):
    """
    Rebuild embeddings for all memories or for a specific character
    
    Args:
        character_id: Optional character ID to filter by
    """
    print("Rebuilding memory embeddings...")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DB_NAME]
    
    # Build query
    query = {}
    if character_id:
        query["character_id"] = character_id
    
    # Get memories
    collection = db[memory_service.memory_collection]
    cursor = collection.find(query)
    memories = await cursor.to_list(length=1000)
    
    print(f"Found {len(memories)} memories to rebuild embeddings for")
    
    # Delete existing embeddings
    embeddings_collection = db[memory_service.embeddings_collection]
    if character_id:
        await embeddings_collection.delete_many({"character_id": character_id})
    else:
        await embeddings_collection.delete_many({})
    
    # Rebuild embeddings
    for i, memory in enumerate(memories):
        memory_id = str(memory["_id"])
        content = memory.get("content", "")
        char_id = memory.get("character_id", "unknown")
        
        # Generate new embedding
        embedding = await memory_service.create_embedding(content)
        
        # Store new embedding
        embedding_doc = {
            "memory_id": memory_id,
            "character_id": char_id,
            "embedding": embedding,
            "created_at": datetime.utcnow()
        }
        
        await embeddings_collection.insert_one(embedding_doc)
        
        if (i + 1) % 10 == 0:
            print(f"Rebuilt {i + 1}/{len(memories)} embeddings")
    
    print(f"Successfully rebuilt {len(memories)} embeddings")
    
    # Close MongoDB connection
    client.close()

async def export_memories(character_id: Optional[str] = None, output_file: str = "memories_export.json"):
    """
    Export memories to a JSON file
    
    Args:
        character_id: Optional character ID to filter by
        output_file: Path to output JSON file
    """
    import json
    
    print(f"Exporting memories to {output_file}...")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DB_NAME]
    
    # Build query
    query = {}
    if character_id:
        query["character_id"] = character_id
    
    # Get memories
    collection = db[memory_service.memory_collection]
    cursor = collection.find(query)
    memories = await cursor.to_list(length=1000)
    
    print(f"Found {len(memories)} memories to export")
    
    # Convert ObjectId to string for JSON serialization
    for memory in memories:
        memory["_id"] = str(memory["_id"])
        memory["created_at"] = memory["created_at"].isoformat()
        memory["last_accessed"] = memory["last_accessed"].isoformat()
    
    # Write to file
    with open(output_file, "w") as f:
        json.dump(memories, f, indent=2)
    
    print(f"Successfully exported {len(memories)} memories to {output_file}")
    
    # Close MongoDB connection
    client.close()

async def main():
    """Main entry point for the CLI"""
    parser = argparse.ArgumentParser(description="Memory Management Utility")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Prune command
    prune_parser = subparsers.add_parser("prune", help="Prune old memories")
    prune_parser.add_argument("--character", help="Character ID to filter by")
    prune_parser.add_argument("--days", type=int, default=30, help="Remove memories older than this many days")
    prune_parser.add_argument("--max-access", type=int, default=0, help="Only remove memories with access count <= this")
    prune_parser.add_argument("--execute", action="store_true", help="Actually delete (default is dry run)")
    
    # Rebuild command
    rebuild_parser = subparsers.add_parser("rebuild", help="Rebuild memory embeddings")
    rebuild_parser.add_argument("--character", help="Character ID to filter by")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export memories to JSON")
    export_parser.add_argument("--character", help="Character ID to filter by")
    export_parser.add_argument("--output", default="memories_export.json", help="Output file path")
    
    args = parser.parse_args()
    
    if args.command == "prune":
        await prune_memories(args.character, args.days, args.max_access, not args.execute)
    elif args.command == "rebuild":
        await rebuild_embeddings(args.character)
    elif args.command == "export":
        await export_memories(args.character, args.output)
    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main()) 