"""
LangGraph Orchestration Module for dialogue flow
"""
from typing import Dict, List, Any, TypedDict, Annotated, Optional
from enum import Enum
import os
from datetime import datetime
from dotenv import load_dotenv
from groq import AsyncGroq
from langgraph.graph import StateGraph, END
import json
from motor.motor_asyncio import AsyncIOMotorClient

from app.schemas.knowledge import KnowledgeQuery
from app.services.knowledge import knowledge_service
from app.services.prompts import prompt_service
from app.memory.service import memory_service

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "hero_agent")
CHARACTER_COLLECTION = "characters"

# Define the state for the graph
class GraphState(TypedDict):
    """State for the dialogue graph"""
    # Input fields
    user_input: str
    character_id: str
    conversation_id: Optional[str]
    prompt_version_id: Optional[str]
    context: Dict[str, Any]
    
    # Working fields
    knowledge_context: List[Dict[str, Any]]
    character_memories: List[Dict[str, Any]]
    character_info: Dict[str, Any]
    conversation_history: List[Dict[str, Any]]
    assembled_context: str
    
    # Output fields
    response: str
    updated_memory: Dict[str, Any]
    completed: bool
    error: Optional[str]

class NodeNames(str, Enum):
    """Node names for the graph"""
    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"
    MEMORY_RETRIEVAL = "memory_retrieval"
    CONTEXT_ASSEMBLY = "context_assembly"
    DIALOGUE_GENERATION = "dialogue_generation"
    MEMORY_INTEGRATION = "memory_integration"

# Initialize the LLM using AsyncGroq directly
llm = AsyncGroq(api_key=GROQ_API_KEY)

# MongoDB client
mongo_client = AsyncIOMotorClient(MONGODB_URI)
db = mongo_client[DB_NAME]

# Node functions
async def knowledge_retrieval(state: GraphState) -> GraphState:
    """
    Knowledge Retrieval Node: Fetch relevant knowledge from vector DB
    """
    try:
        # Get character info from database
        character_id = state["character_id"]
        
        try:
            # Get character info from database
            collection = db[CHARACTER_COLLECTION]
            character_result = await collection.find_one({"_id": character_id})
            
            if character_result:
                character_info = {
                    "name": character_result.get("name", character_id),
                    "description": character_result.get("description", ""),
                    "personality": character_result.get("personality", ""),
                    "knowledge_base": character_result.get("knowledge_base", "")
                }
            else:
                # Fallback character info
                character_info = {
                    "name": character_id,
                    "description": "A fictional character",
                    "personality": "Friendly and helpful",
                    "knowledge_base": ""
                }
            
            # Create knowledge query
            query_text = f"{state['user_input']} Context: Character is {character_info.get('name', '')}."
            
            # Extract character name from ID for filtering
            if character_id.startswith('character_'):
                # Extract name from ID (e.g., character_iron_man -> Iron Man)
                character_name = character_id.replace('character_', '').replace('_', ' ').title()
                print(f"Searching for knowledge with character: {character_name}")
                filter_metadata = {"character": character_name}
            else:
                filter_metadata = {"character": character_info.get('name', '')}
            
            # Create knowledge query
            knowledge_query = KnowledgeQuery(
                query=query_text,
                top_k=5,  # Increased from 3 to 5 for more comprehensive knowledge
                filter_metadata=filter_metadata
            )
            
            # Use knowledge service to retrieve relevant knowledge
            knowledge_chunks = await knowledge_service.retrieve_similar(db, knowledge_query)
            print(f"Retrieved {len(knowledge_chunks)} knowledge chunks for query: '{query_text}'")
            if knowledge_chunks:
                for i, chunk in enumerate(knowledge_chunks):
                    print(f"Chunk {i+1}: {chunk.content[:100]}... [score: {chunk.metadata.get('similarity_score', 0)}]")
            
            # Convert to dictionaries if needed
            if knowledge_chunks:
                knowledge_chunks = [chunk.dict() for chunk in knowledge_chunks]
            else:
                knowledge_chunks = []
            
            # Update state
            state["knowledge_context"] = knowledge_chunks
            state["character_info"] = character_info
            
            # Retrieve conversation history if conversation_id provided
            conversation_history = []
            if state.get("conversation_id"):
                try:
                    collection = db["conversations"]
                    result = await collection.find_one(
                        {"_id": state["conversation_id"]},
                        {"messages": {"$slice": -5}}  # Get last 5 messages
                    )
                    
                    if result and "messages" in result:
                        conversation_history = result["messages"]
                except Exception as e:
                    print(f"Error retrieving conversation history: {str(e)}")
            
            state["conversation_history"] = conversation_history
            
        except Exception as knowledge_error:
            print(f"Error retrieving knowledge: {str(knowledge_error)}")
            state["knowledge_context"] = []
            state["character_info"] = {
                "name": character_id,
                "description": "A fictional character",
                "personality": "Friendly and helpful"
            }
            state["conversation_history"] = []
            state["error"] = f"Knowledge retrieval error: {str(knowledge_error)}"
        
    except Exception as e:
        print(f"Error in knowledge_retrieval node: {str(e)}")
        state["error"] = f"Knowledge retrieval error: {str(e)}"
        state["knowledge_context"] = []
        state["character_info"] = {
            "name": character_id,
            "description": "A fictional character",
            "personality": "Friendly and helpful"
        }
        state["conversation_history"] = []
    
    return state

async def memory_retrieval(state: GraphState) -> GraphState:
    """
    Memory Retrieval Node: Fetch relevant memories for the character
    """
    try:
        character_id = state["character_id"]
        user_input = state["user_input"]
        
        # Search for relevant memories using the memory service
        try:
            character_memories = await memory_service.search_memories(
                db, 
                character_id, 
                user_input, 
                limit=3
            )
            
            # If no memories found with search, get most important memories
            if not character_memories:
                character_memories = await memory_service.get_character_memories(
                    db,
                    character_id,
                    limit=3,
                    sort_by="importance"
                )
                
            # Ensure character_memories is a list of dictionaries
            if not isinstance(character_memories, list):
                character_memories = []
                
            # Update state
            state["character_memories"] = character_memories
            
        except Exception as memory_error:
            print(f"Error retrieving memories: {str(memory_error)}")
            state["error"] = f"Memory retrieval error: {str(memory_error)}"
            state["character_memories"] = []
        
    except Exception as e:
        print(f"Error in memory_retrieval node: {str(e)}")
        state["error"] = f"Memory retrieval error: {str(e)}"
        state["character_memories"] = []
    
    return state

async def context_assembly(state: GraphState) -> GraphState:
    """
    Context Assembly Node: Organize knowledge and context for LLM prompt
    """
    try:
        # Ensure required fields exist
        if "knowledge_context" not in state or not state["knowledge_context"]:
            state["knowledge_context"] = []
        
        if "character_info" not in state or not state["character_info"]:
            character_id = state.get("character_id", "unknown")
            state["character_info"] = {
                "name": character_id,
                "description": "A fictional character",
                "personality": "Friendly and helpful"
            }
        
        if "conversation_history" not in state:
            state["conversation_history"] = []
        
        # Format knowledge context
        knowledge_text = ""
        if state["knowledge_context"]:
            knowledge_text = "RELEVANT KNOWLEDGE CHUNKS (USE ONLY THIS INFORMATION):\n\n"
            for i, chunk in enumerate(state["knowledge_context"]):
                content = chunk.get('content', 'No content available')
                source = chunk.get('metadata', {}).get('source', 'Unknown source')
                score = chunk.get('metadata', {}).get('similarity_score', 'N/A')
                knowledge_text += f"CHUNK {i+1}: {content}\nSource: {source}\nRelevance Score: {score}\n\n"
        else:
            knowledge_text = "NO KNOWLEDGE CHUNKS AVAILABLE. Inform the user you don't have specific information about their query in your knowledge base."
        
        # Format character memories
        memories_text = ""
        if "character_memories" in state and state["character_memories"]:
            memories_text = "Character memories:\n"
            for memory in state["character_memories"]:
                memories_text += f"- {memory.get('content', 'No memory content')}\n"
        
        # Format character info
        character_info = state["character_info"]
        character_text = f"Character: {character_info.get('name', 'Character')}\n"
        character_text += f"Description: {character_info.get('description', 'No description')}\n"
        character_text += f"Personality: {character_info.get('personality', 'No personality defined')}\n"
        
        # Format conversation history (if any)
        history_text = ""
        if state["conversation_history"]:
            history_text = "Previous conversation:\n"
            for msg in state["conversation_history"]:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                history_text += f"{role.capitalize()}: {content}\n"
        
        # Combine everything into assembled context
        assembled_context = f"""
CHARACTER INFORMATION:
{character_text}

KNOWLEDGE CONTEXT:
{knowledge_text}

{memories_text}

{history_text}

USER INPUT:
{state.get('user_input', 'No user input')}
"""
        
        # Update state
        state["assembled_context"] = assembled_context
        
    except Exception as e:
        state["error"] = f"Context assembly error: {str(e)}"
        state["assembled_context"] = f"Error assembling context: {str(e)}"
    
    return state

async def dialogue_generation(state: GraphState) -> GraphState:
    """
    Dialogue Generation Node: Generate character response using LLM
    """
    try:
        # Get prompt template
        prompt_version_id = state.get("prompt_version_id")
        # This would normally fetch from DB using prompt_service
        
        # Default prompt template
        prompt_template = """You are {character_name}, {character_description}.
Respond in character with the personality: {character_personality}.

EXTREMELY IMPORTANT INSTRUCTIONS:
1. You MUST ONLY use the knowledge provided below to answer the user's question.
2. If the knowledge doesn't contain information to answer the question, say "I don't have specific information about that in my knowledge base."
3. DO NOT use your pre-trained knowledge to answer questions about the character or their universe.
4. ONLY respond based on the knowledge context provided.
5. DO NOT MAKE UP ANY INFORMATION that is not explicitly provided in the knowledge context.
6. If you're unsure about something, say you don't have that information rather than guessing.

KNOWLEDGE CONTEXT:
{knowledge_context}

{conversation_history}
User: {user_input}
{character_name}:"""
        
        # Ensure character_info exists
        if "character_info" not in state or not state["character_info"]:
            character_id = state.get("character_id", "unknown")
            state["character_info"] = {
                "name": character_id,
                "description": "A fictional character",
                "personality": "Friendly and helpful"
            }
        
        # Format prompt
        formatted_prompt = prompt_template.format(
            character_name=state["character_info"].get("name", "Character"),
            character_description=state["character_info"].get("description", "A fictional character"),
            character_personality=state["character_info"].get("personality", "Friendly and helpful"),
            knowledge_context=state.get("assembled_context", "No specific knowledge available."),
            conversation_history=state.get("conversation_history", ""),
            user_input=state.get("user_input", "Hello")
        )
        
        # Generate response using Groq API
        response = await llm.chat.completions.create(
            model="llama3-70b-8192",  # Use a model that exists in Groq
            messages=[
                {
                    "role": "system", 
                    "content": "You are a character in a dialogue system. You MUST ONLY use the knowledge provided in the user's message to answer questions. DO NOT use your pre-trained knowledge. If the knowledge doesn't contain information to answer the question, say you don't have that information."
                },
                {"role": "user", "content": formatted_prompt}
            ],
            temperature=0.2,  # Lower temperature for more deterministic responses
            max_tokens=300
        )
        
        # Extract response content
        ai_response = response.choices[0].message.content
        
        # Update state
        state["response"] = ai_response
        
    except Exception as e:
        state["error"] = f"Dialogue generation error: {str(e)}"
        state["response"] = "I'm sorry, I'm having trouble responding right now."
    
    return state

async def memory_integration(state: GraphState) -> GraphState:
    """
    Memory Integration Node: Update character memory based on interaction
    """
    try:
        # Skip memory integration if there was an error in previous steps
        if state.get("error"):
            print(f"Skipping memory integration due to previous error: {state.get('error')}")
            state["completed"] = True
            state["updated_memory"] = {}
            return state
            
        # Ensure we have a response to store
        if not state.get("response"):
            state["error"] = "No response to store in memory"
            state["completed"] = True
            state["updated_memory"] = {}
            return state
            
        # Create memory from the interaction
        memory_content = f"User asked: '{state.get('user_input', '')}'. I responded: '{state.get('response', '')}'"
        
        try:
            # Store the memory in MongoDB
            character_id = state["character_id"]
            
            # Create the memory using the memory service
            memory_id = await memory_service.create_memory(
                db,
                character_id,
                memory_content,
                "conversation",
                5,  # Medium importance
                {
                    "conversation_id": state.get("conversation_id"),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Get the created memory
            new_memory = await memory_service.get_memory(db, memory_id)
            
            # Update state
            state["updated_memory"] = new_memory or {}
            state["completed"] = True
            
        except Exception as memory_error:
            print(f"Error storing memory: {str(memory_error)}")
            state["error"] = f"Memory integration error: {str(memory_error)}"
            state["updated_memory"] = {}
            state["completed"] = True
        
    except Exception as e:
        print(f"Error in memory_integration node: {str(e)}")
        state["error"] = f"Memory integration error: {str(e)}"
        state["updated_memory"] = {}
        state["completed"] = True
    
    return state

def create_dialogue_graph() -> StateGraph:
    """
    Create the dialogue graph with all nodes
    """
    # Initialize the graph
    workflow = StateGraph(GraphState)
    
    # Add nodes
    workflow.add_node(NodeNames.KNOWLEDGE_RETRIEVAL, knowledge_retrieval)
    workflow.add_node(NodeNames.MEMORY_RETRIEVAL, memory_retrieval)
    workflow.add_node(NodeNames.CONTEXT_ASSEMBLY, context_assembly)
    workflow.add_node(NodeNames.DIALOGUE_GENERATION, dialogue_generation)
    workflow.add_node(NodeNames.MEMORY_INTEGRATION, memory_integration)
    
    # Define edges
    workflow.add_edge(NodeNames.KNOWLEDGE_RETRIEVAL, NodeNames.MEMORY_RETRIEVAL)
    workflow.add_edge(NodeNames.MEMORY_RETRIEVAL, NodeNames.CONTEXT_ASSEMBLY)
    workflow.add_edge(NodeNames.CONTEXT_ASSEMBLY, NodeNames.DIALOGUE_GENERATION)
    workflow.add_edge(NodeNames.DIALOGUE_GENERATION, NodeNames.MEMORY_INTEGRATION)
    workflow.add_edge(NodeNames.MEMORY_INTEGRATION, END)
    
    # Set entry point
    workflow.set_entry_point(NodeNames.KNOWLEDGE_RETRIEVAL)
    
    # Compile the graph
    return workflow.compile()

# Create the dialogue graph
dialogue_graph = create_dialogue_graph()

async def generate_dialogue_response(
    user_input: str,
    character_id: str,
    conversation_id: Optional[str] = None,
    prompt_version_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate a dialogue response using the LangGraph workflow
    
    Args:
        user_input: User's message
        character_id: ID of the character
        conversation_id: Optional ID of the conversation
        prompt_version_id: Optional ID of the prompt version to use
        context: Optional additional context
        
    Returns:
        Dictionary with response and additional information
    """
    # Create initial state
    initial_state = GraphState(
        user_input=user_input,
        character_id=character_id,
        conversation_id=conversation_id,
        prompt_version_id=prompt_version_id,
        context=context or {},
        knowledge_context=[],
        character_memories=[],
        character_info={},
        conversation_history=[],
        assembled_context="",
        response="",
        updated_memory={},
        completed=False,
        error=None
    )
    
    # Execute the graph
    result = await dialogue_graph.ainvoke(initial_state)
    
    # Check if there was an error during processing
    if result.get("error"):
        print(f"Error in dialogue generation: {result.get('error')}")
        response_data = {
            "response": f"I'm sorry, I'm having trouble responding right now. Error: {result.get('error')}",
            "conversation_id": result.get("conversation_id"),
            "knowledge_used": [],
            "memories_used": [],
            "updated_memory": {},
            "error": result.get("error")
        }
        return response_data
    
    # Extract relevant information from result
    response_data = {
        "response": result.get("response", "I'm sorry, I couldn't generate a response at this time."),
        "conversation_id": result.get("conversation_id"),
        "knowledge_used": [chunk.get("id") for chunk in result.get("knowledge_context", []) if isinstance(chunk, dict) and "id" in chunk],
        "memories_used": [memory.get("id") for memory in result.get("character_memories", []) if isinstance(memory, dict) and "id" in memory],
        "updated_memory": result.get("updated_memory", {}),
        "error": result.get("error")
    }
    
    return response_data 