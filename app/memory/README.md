# Character Long-Term Memory System

This module provides long-term memory capabilities for character agents in the Hero Agent system.

## Overview

The memory system allows characters to:
- Store memories from conversations and external sources (like Wikipedia)
- Retrieve relevant memories based on semantic search
- Use memories to provide more contextual and personalized responses

## Components

- `service.py`: Core memory service with CRUD operations and semantic search
- `create_index.py`: Script to create MongoDB vector search index
- `load_all_memories.py`: Script to load memories for all characters
- `add_test_memories.py`: Script to add test memories for development
- `memory_analytics.py`: Script for analyzing memory usage patterns
- `memory_management.py`: Utility for memory maintenance tasks
- `characters/`: Character-specific memory folders
  - `iron_man/`: Iron Man memory data and loaders
  - `thor/`: Thor memory data and loaders

## Setup Instructions

1. Ensure MongoDB Atlas is configured with your connection string in `.env`
2. Create the vector search index:
   ```
   python -m app.memory.create_index
   ```
3. Load initial memories:
   ```
   python -m app.memory.add_test_memories
   ```

## Memory Structure

Each memory contains:
- `character_id`: ID of the character the memory belongs to
- `content`: The actual memory content
- `source`: Source of the memory (conversation, wikipedia, etc.)
- `importance`: Importance score (1-10)
- `metadata`: Additional metadata about the memory
  - `topic`: Topic of the memory
  - `emotion`: Emotional context of the memory
  - `category`: Category for organization (core, personal, avengers, etc.)
- `created_at`: Creation timestamp
- `last_accessed`: Last access timestamp
- `access_count`: Number of times this memory has been accessed

## API Endpoints

The memory system provides the following API endpoints:

- `POST /memory/create`: Create a new memory
- `GET /memory/{memory_id}`: Get a memory by ID
- `POST /memory/search`: Search memories by semantic similarity
- `GET /memory/character/{character_id}`: Get memories for a character
- `PUT /memory/{memory_id}`: Update a memory
- `DELETE /memory/{memory_id}`: Delete a memory

## Integration with Dialogue Flow

The memory system is integrated with the LangGraph dialogue flow:
1. User sends a message
2. System retrieves relevant memories based on the query
3. Memories are included in the context for response generation
4. New memories are created from the interaction

## Memory Search

The system uses two search methods:
1. Vector search using Groq embeddings and MongoDB Atlas vector search (primary)
2. Regex pattern matching as a fallback when vector search is unavailable

## Memory Management

The `memory_management.py` utility provides tools for memory maintenance:

```
# Prune old, unused memories
python -m app.memory.memory_management prune --character iron_man --days 30 --max-access 0 --execute

# Rebuild embeddings for a character
python -m app.memory.memory_management rebuild --character thor

# Export memories to JSON
python -m app.memory.memory_management export --character iron_man --output iron_man_memories.json
```

## Memory Analytics

The `memory_analytics.py` script provides insights into memory usage:

```
python -m app.memory.memory_analytics
```

This will show:
- Total memories per character
- Distribution by source, importance, and category
- Access patterns and most frequently accessed memories
- Recent memory creation statistics

## Rate Limiting

The system uses Groq API for embeddings which has a limit of 6000 tokens per minute. The memory service handles rate limiting to ensure we stay within these constraints. 