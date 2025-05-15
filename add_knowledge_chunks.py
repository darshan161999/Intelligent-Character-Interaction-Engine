#!/usr/bin/env python
"""
Script to add knowledge chunks for Marvel characters from Wikipedia
"""
import asyncio
import os
import re
import requests
from bs4 import BeautifulSoup
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from app.schemas.knowledge import KnowledgeChunk
from app.services.knowledge import knowledge_service

# Load environment variables
load_dotenv()

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://nemaded:34VjOgwdQPPgW45M@cluster0.urtxinp.mongodb.net/")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "hero_agent")

# Character Wikipedia URLs
CHARACTERS = {
    "Iron Man": {
        "url": "https://en.wikipedia.org/wiki/Iron_Man",
        "sections": ["Publication history", "Fictional character biography", "Powers and abilities", "Supporting characters", "Cultural impact"]
    },
    "Thor": {
        "url": "https://en.wikipedia.org/wiki/Thor_(Marvel_Comics)",
        "sections": ["Publication history", "Fictional character biography", "Powers and abilities", "Supporting characters", "Cultural impact"]
    }
}

def clean_text(text):
    """Clean the text by removing citations, extra whitespace, etc."""
    # Remove citations
    text = re.sub(r'\[\d+\]', '', text)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove edit links
    text = re.sub(r'\[edit\]', '', text)
    return text.strip()

def get_wikipedia_content(url, sections):
    """Fetch content from Wikipedia for specified sections"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        content = {}
        
        # Get all section headers
        headers = soup.find_all(['h1', 'h2', 'h3', 'h4'])
        
        for section in sections:
            section_content = []
            found_section = False
            
            # Find the section header
            for i, header in enumerate(headers):
                if section.lower() in header.text.lower():
                    found_section = True
                    next_header_idx = i + 1
                    
                    # Get all paragraphs until the next section header
                    current = header.find_next()
                    while current and (next_header_idx >= len(headers) or current != headers[next_header_idx]):
                        if current.name == 'p' and len(current.text.strip()) > 50:  # Only paragraphs with substantial content
                            section_content.append(clean_text(current.text))
                        current = current.find_next()
                    
                    break
            
            if found_section and section_content:
                content[section] = section_content
        
        return content
    
    except Exception as e:
        print(f"Error fetching Wikipedia content: {str(e)}")
        return {}

def chunk_text(text, max_chunk_size=500, overlap=50):
    """Split text into chunks of specified size with overlap"""
    chunks = []
    for i in range(0, len(text), max_chunk_size - overlap):
        # Extract chunk text
        chunk_text = text[i:i + max_chunk_size]
        
        # If this isn't the first chunk and we have overlap, adjust start
        if i > 0 and overlap > 0:
            chunk_text = text[i - overlap:i + max_chunk_size - overlap]
        
        chunks.append(chunk_text)
    
    return chunks

async def add_knowledge_chunks():
    """Add knowledge chunks to the database from Wikipedia"""
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[MONGODB_DB_NAME]
    
    # Clear existing knowledge chunks
    print("Clearing existing knowledge chunks...")
    await db.knowledge_chunks.delete_many({})
    
    # Process each character
    for character, info in CHARACTERS.items():
        print(f"\nFetching Wikipedia content for {character}...")
        content = get_wikipedia_content(info["url"], info["sections"])
        
        if not content:
            print(f"No content found for {character}")
            continue
        
        print(f"Found content for {len(content)} sections")
        
        # Process each section
        for section, paragraphs in content.items():
            print(f"Processing section: {section}")
            
            for paragraph in paragraphs:
                # Skip short paragraphs
                if len(paragraph) < 100:
                    continue
                
                # Create chunks from paragraph
                text_chunks = chunk_text(paragraph)
                
                for text in text_chunks:
                    # Create knowledge chunk
                    chunk = KnowledgeChunk(
                        content=text,
                        source=f"Wikipedia - {character} - {section}",
                        metadata={
                            "character": character,
                            "topic": section,
                            "source": "Wikipedia"
                        }
                    )
                    
                    # Store chunk
                    chunk_id = await knowledge_service.store_chunk(db, chunk)
                    print(f"Added chunk: {chunk_id[:8]}... ({len(text)} chars)")
    
    # Verify counts
    count = await db.knowledge_chunks.count_documents({})
    print(f"\nTotal knowledge chunks in database: {count}")
    
    # Close connection
    client.close()

if __name__ == "__main__":
    asyncio.run(add_knowledge_chunks()) 