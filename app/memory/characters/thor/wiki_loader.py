"""
Script to load Thor data from Wikipedia into memory database
"""
import os
import asyncio
import json
from typing import List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
import wikipedia
from dotenv import load_dotenv

from app.memory.service import memory_service

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "hero_agent")
CHARACTER_ID = "thor"  # Character ID for Thor
WIKI_PAGES = [
    "Thor (Marvel Comics)",
    "Thor (Marvel Cinematic Universe)",
    "Thor (film)",
    "Thor: The Dark World",
    "Thor: Ragnarok",
    "Thor: Love and Thunder",
    "Asgard (comics)"
]

async def fetch_wikipedia_content(page_title: str) -> Dict[str, Any]:
    """
    Fetch content from Wikipedia
    
    Args:
        page_title: Title of the Wikipedia page
        
    Returns:
        Dictionary with page content and metadata
    """
    try:
        # Get Wikipedia page
        page = wikipedia.page(page_title)
        
        # Get content and split into sections
        content = page.content
        sections = []
        
        # Simple section splitting by == headers ==
        current_section = {"title": "Summary", "content": ""}
        for line in content.split('\n'):
            if line.startswith('== ') and line.endswith(' =='):
                # Save previous section if not empty
                if current_section["content"].strip():
                    sections.append(current_section)
                
                # Start new section
                section_title = line.strip('= ')
                current_section = {"title": section_title, "content": ""}
            else:
                # Add line to current section
                current_section["content"] += line + "\n"
        
        # Add the last section
        if current_section["content"].strip():
            sections.append(current_section)
        
        return {
            "title": page.title,
            "url": page.url,
            "sections": sections
        }
    except Exception as e:
        print(f"Error fetching Wikipedia content for {page_title}: {str(e)}")
        return {
            "title": page_title,
            "url": "",
            "sections": [{"title": "Error", "content": f"Failed to fetch content: {str(e)}"}]
        }

async def store_memory(
    db: AsyncIOMotorClient,
    character_id: str,
    content: str,
    source: str,
    importance: int,
    metadata: Dict[str, Any]
) -> str:
    """
    Store a memory in the database
    
    Args:
        db: Database client
        character_id: Character ID
        content: Memory content
        source: Source of the memory
        importance: Importance score
        metadata: Additional metadata
        
    Returns:
        ID of the created memory
    """
    try:
        memory_id = await memory_service.create_memory(
            db,
            character_id,
            content,
            source,
            importance,
            metadata
        )
        return memory_id
    except Exception as e:
        print(f"Error storing memory: {str(e)}")
        return ""

async def process_wiki_page(db: AsyncIOMotorClient, character_id: str, page_title: str) -> List[str]:
    """
    Process a Wikipedia page and store its content as memories
    
    Args:
        db: Database client
        character_id: Character ID
        page_title: Wikipedia page title
        
    Returns:
        List of created memory IDs
    """
    print(f"Processing Wikipedia page: {page_title}")
    wiki_data = await fetch_wikipedia_content(page_title)
    memory_ids = []
    
    # Store each section as a separate memory
    for section in wiki_data["sections"]:
        # Skip empty sections
        if not section["content"].strip():
            continue
        
        # Determine importance based on section title
        importance = 8 if section["title"] == "Summary" else 5
        
        # Create metadata
        metadata = {
            "wiki_page": wiki_data["title"],
            "wiki_url": wiki_data["url"],
            "section": section["title"]
        }
        
        # Store memory
        memory_id = await store_memory(
            db,
            character_id,
            section["content"],
            f"wikipedia:{wiki_data['title']}",
            importance,
            metadata
        )
        
        if memory_id:
            memory_ids.append(memory_id)
            print(f"Created memory {memory_id} for section '{section['title']}'")
    
    return memory_ids

async def main():
    """Main function to load Wikipedia data"""
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DB_NAME]
    
    print(f"Connected to MongoDB at {MONGODB_URI}")
    print(f"Loading Wikipedia data for character: {CHARACTER_ID}")
    
    # Process each Wikipedia page
    all_memory_ids = []
    for page_title in WIKI_PAGES:
        memory_ids = await process_wiki_page(db, CHARACTER_ID, page_title)
        all_memory_ids.extend(memory_ids)
    
    print(f"Completed loading {len(all_memory_ids)} memories for {CHARACTER_ID}")
    
    # Close MongoDB connection
    client.close()

if __name__ == "__main__":
    asyncio.run(main()) 