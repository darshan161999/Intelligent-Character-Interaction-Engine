"""
Script to analyze memory usage and access patterns
"""
import asyncio
import sys
import os
from typing import Dict, Any, List
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from collections import Counter

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.memory.service import memory_service

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "hero_agent")

async def analyze_memories():
    """Analyze memory usage and access patterns"""
    print("Analyzing character memories...")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DB_NAME]
    
    print(f"Connected to MongoDB at {MONGODB_URI}")
    
    # Get all characters
    collection = db[memory_service.memory_collection]
    characters = await collection.distinct("character_id")
    
    for character_id in characters:
        print(f"\n=== Memory Analysis for {character_id} ===")
        
        # Get all memories for this character
        cursor = collection.find({"character_id": character_id})
        memories = await cursor.to_list(length=1000)
        
        if not memories:
            print(f"No memories found for {character_id}")
            continue
        
        print(f"Total memories: {len(memories)}")
        
        # Analyze memory sources
        sources = Counter([memory.get("source", "unknown") for memory in memories])
        print("\nMemory sources:")
        for source, count in sources.most_common():
            print(f"- {source}: {count}")
        
        # Analyze memory importance
        importance_levels = Counter([memory.get("importance", 0) for memory in memories])
        print("\nImportance distribution:")
        for level in sorted(importance_levels.keys()):
            print(f"- Level {level}: {importance_levels[level]}")
        
        # Analyze memory categories (if available)
        categories = Counter([
            memory.get("metadata", {}).get("category", "uncategorized") 
            for memory in memories
        ])
        print("\nMemory categories:")
        for category, count in categories.most_common():
            print(f"- {category}: {count}")
        
        # Analyze access patterns
        accessed_memories = [m for m in memories if m.get("access_count", 0) > 0]
        print(f"\nAccessed memories: {len(accessed_memories)} ({len(accessed_memories)/len(memories)*100:.1f}%)")
        
        if accessed_memories:
            avg_access = sum(m.get("access_count", 0) for m in memories) / len(memories)
            print(f"Average access count: {avg_access:.2f}")
            
            # Most accessed memories
            top_accessed = sorted(memories, key=lambda m: m.get("access_count", 0), reverse=True)[:3]
            print("\nMost accessed memories:")
            for memory in top_accessed:
                print(f"- [{memory.get('access_count', 0)} accesses] {memory.get('content', '')[:50]}...")
        
        # Analyze recency
        now = datetime.utcnow()
        recent_memories = [
            m for m in memories 
            if m.get("created_at") and (now - m["created_at"]) < timedelta(days=7)
        ]
        print(f"\nRecent memories (last 7 days): {len(recent_memories)}")
        
    # Close MongoDB connection
    client.close()
    print("\nAnalysis completed!")

if __name__ == "__main__":
    asyncio.run(analyze_memories()) 