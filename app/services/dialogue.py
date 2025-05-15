"""
Dialogue Service for managing conversations and generating responses
"""
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from groq import AsyncGroq
from dotenv import load_dotenv
from bson import ObjectId

from app.schemas.dialogue import Message, Conversation, DialogueRequest, DialogueResponse
from app.schemas.knowledge import KnowledgeQuery
from app.services.knowledge import knowledge_service
from app.services.prompts import prompt_service

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

class DialogueService:
    """Service for managing character dialogues and conversations"""
    
    def __init__(
        self,
        conversation_collection: str = "conversations",
        character_collection: str = "characters",
        api_key: Optional[str] = None
    ):
        """Initialize the dialogue service"""
        self.conversation_collection = conversation_collection
        self.character_collection = character_collection
        self.api_key = api_key or GROQ_API_KEY
        self.client = AsyncGroq(api_key=self.api_key)
        self.model = "llama3-70b-8192"  # Default model
        
        # Character ID to name mapping for knowledge retrieval
        self.character_id_map = {
            "character_iron_man": "Iron Man",
            "character_thor": "Thor",
            "character_captain_america": "Captain America",
            "character_black_widow": "Black Widow",
            "character_hulk": "Hulk"
        }
    
    # Conversation Management
    
    async def create_conversation(
        self,
        db: AsyncIOMotorDatabase,
        participant_ids: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new conversation
        
        Args:
            db: AsyncIOMotorDatabase instance
            participant_ids: List of participant IDs
            metadata: Optional metadata for the conversation
            
        Returns:
            ID of the created conversation
        """
        conversation = Conversation(
            participant_ids=participant_ids,
            metadata=metadata or {}
        )
        
        collection = db[self.conversation_collection]
        result = await collection.insert_one(conversation.dict())
        return str(result.inserted_id)
    
    async def get_conversation(
        self,
        db: AsyncIOMotorDatabase,
        conversation_id: Any
    ) -> Optional[Conversation]:
        """
        Get a conversation by ID
        
        Args:
            db: AsyncIOMotorDatabase instance
            conversation_id: ID of the conversation (ObjectId or string)
            
        Returns:
            The conversation or None if not found
        """
        collection = db[self.conversation_collection]
        
        # Ensure conversation_id is an ObjectId
        if isinstance(conversation_id, str):
            try:
                conversation_id = ObjectId(conversation_id)
            except Exception:
                # If conversion fails, try with the string as is
                pass
        
        result = await collection.find_one({"_id": conversation_id})
        
        if result:
            result["id"] = str(result.pop("_id"))
            return Conversation(**result)
        return None
    
    async def add_message(
        self,
        db: AsyncIOMotorDatabase,
        conversation_id: Any,
        message: Message
    ) -> bool:
        """
        Add a message to a conversation
        
        Args:
            db: AsyncIOMotorDatabase instance
            conversation_id: ID of the conversation (ObjectId or string)
            message: Message to add
            
        Returns:
            True if successful, False otherwise
        """
        collection = db[self.conversation_collection]
        
        # Ensure conversation_id is an ObjectId
        if isinstance(conversation_id, str):
            try:
                conversation_id = ObjectId(conversation_id)
            except Exception:
                # If conversion fails, try with the string as is
                pass
        
        result = await collection.update_one(
            {"_id": conversation_id},
            {
                "$push": {"messages": message.dict()},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        return result.modified_count > 0
    
    async def get_recent_messages(
        self,
        db: AsyncIOMotorDatabase,
        conversation_id: Any,
        limit: int = 10
    ) -> List[Message]:
        """
        Get most recent messages from a conversation
        
        Args:
            db: AsyncIOMotorDatabase instance
            conversation_id: ID of the conversation (ObjectId or string)
            limit: Maximum number of messages to return
            
        Returns:
            List of messages
        """
        collection = db[self.conversation_collection]
        
        # Ensure conversation_id is an ObjectId
        if isinstance(conversation_id, str):
            try:
                conversation_id = ObjectId(conversation_id)
            except Exception:
                # If conversion fails, try with the string as is
                pass
        
        result = await collection.find_one(
            {"_id": conversation_id},
            {"messages": {"$slice": -limit}}
        )
        
        if result and "messages" in result:
            return [Message(**msg) for msg in result["messages"]]
        return []
    
    # Character Information
    
    async def get_character_info(
        self,
        db: AsyncIOMotorDatabase,
        character_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get information about a character
        
        Args:
            db: AsyncIOMotorDatabase instance
            character_id: ID of the character
            
        Returns:
            Character information or None if not found
        """
        collection = db[self.character_collection]
        result = await collection.find_one({"_id": character_id})
        
        if result:
            result["id"] = str(result.pop("_id"))
            return result
        return None
    
    # Dialogue Generation
    
    async def retrieve_context(
        self,
        db: AsyncIOMotorDatabase,
        request: DialogueRequest
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Retrieve relevant context for a dialogue
        
        Args:
            db: AsyncIOMotorDatabase instance
            request: Dialogue request
            
        Returns:
            Tuple of (knowledge chunks, other context)
        """
        # Get character information
        character_info = await self.get_character_info(db, request.character_id)
        
        # If character info not found, create a default one
        if not character_info:
            character_info = {
                "name": request.character_id,
                "description": "A fictional character",
                "personality": "Friendly and helpful"
            }
        
        # Retrieve conversation history if exists
        conversation_history = []
        if request.conversation_id:
            try:
                conversation_history = await self.get_recent_messages(
                    db, 
                    request.conversation_id, 
                    limit=5
                )
            except Exception as e:
                print(f"Error retrieving conversation history: {str(e)}")
                # Continue with empty history
        
        # Build query from user message and character context
        query_text = f"{request.user_message}"
        if character_info:
            query_text += f" Context: Character is {character_info.get('name', '')}."
        
        # Add metadata filter if available
        filter_metadata = {}
        if request.character_id in self.character_id_map:
            # Use the mapped character name for knowledge retrieval
            character_name = self.character_id_map[request.character_id]
            filter_metadata["character"] = character_name
            print(f"Using character name '{character_name}' for knowledge retrieval")
        else:
            # Fallback to character info name if available
            if character_info and "name" in character_info:
                filter_metadata["character"] = character_info["name"]
        
        # Create knowledge query
        knowledge_query = KnowledgeQuery(
            query=query_text,
            top_k=3,
            filter_metadata=filter_metadata
        )
        
        # Retrieve relevant knowledge
        try:
            knowledge_chunks = await knowledge_service.retrieve_similar(db, knowledge_query)
        except Exception as e:
            print(f"Error retrieving knowledge: {str(e)}")
            knowledge_chunks = []
        
        # Build additional context
        additional_context = {
            "character_info": character_info,
            "conversation_history": [msg.dict() for msg in conversation_history] if conversation_history else [],
            "user_context": request.context or {}
        }
        
        return [chunk.dict() for chunk in knowledge_chunks] if knowledge_chunks else [], additional_context
    
    async def generate_dialogue(
        self,
        db: AsyncIOMotorDatabase,
        request: DialogueRequest
    ) -> DialogueResponse:
        """
        Generate dialogue response
        
        Args:
            db: AsyncIOMotorDatabase instance
            request: Dialogue request
            
        Returns:
            Generated dialogue response
        """
        try:
            # Retrieve knowledge and context
            knowledge_chunks, context = await self.retrieve_context(db, request)
            
            # Get character info
            character_info = context.get("character_info", {})
            character_name = character_info.get("name", "Unknown Character")
            
            # Get conversation history
            conversation_history = context.get("conversation_history", [])
            
            # Get prompt template from database
            prompt_template = None
            if request.prompt_version_id:
                try:
                    prompt_version = await prompt_service.get_version(db, request.prompt_version_id)
                    if prompt_version and hasattr(prompt_version, 'template'):
                        prompt_template = prompt_version.template
                except Exception as e:
                    print(f"Error retrieving prompt version: {str(e)}")
            
            # If no prompt template found, try to get a default for the character
            if not prompt_template:
                try:
                    # Try to get a default prompt for this character
                    default_prompt = await prompt_service.get_default_for_character(db, request.character_id)
                    if default_prompt and hasattr(default_prompt, 'template'):
                        prompt_template = default_prompt.template
                except Exception as e:
                    print(f"Error retrieving default character prompt: {str(e)}")
            
            # If still no prompt template, use the hardcoded default
            if not prompt_template:
                prompt_template = "You are {character_name}, {character_description}. " + \
                                "Respond as this character would, maintaining their personality, " + \
                                "speaking style, and knowledge. " + \
                                "Knowledge context: {knowledge_context}. " + \
                                "Previous conversation: {conversation_history}. " + \
                                "User message: {user_message}"
            
            # Format knowledge context
            knowledge_context = "\n".join([chunk.get("content", "") for chunk in knowledge_chunks]) if knowledge_chunks else "No specific knowledge available."
            
            # Format conversation history
            formatted_history = ""
            for msg in conversation_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                formatted_history += f"{role.capitalize()}: {content}\n"
            
            # Prepare prompt variables
            prompt_variables = {
                "character_name": character_name,
                "character_description": character_info.get("description", ""),
                "knowledge_context": knowledge_context,
                "conversation_history": formatted_history,
                "user_message": request.user_message
            }
            
            # Add any additional context from request
            if request.context:
                for key, value in request.context.items():
                    if isinstance(value, (str, int, float, bool)):
                        prompt_variables[key] = value
            
            # Format the prompt
            prompt = prompt_template
            for key, value in prompt_variables.items():
                placeholder = "{" + key + "}"
                if placeholder in prompt:
                    prompt = prompt.replace(placeholder, str(value))
            
            # Generate response using Groq
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=300
                )
                
                # Extract response text
                response_text = response.choices[0].message.content
                
                # Create conversation if needed
                conversation_id = request.conversation_id
                if not conversation_id:
                    # Create new conversation
                    try:
                        conversation_id = await self.create_conversation(
                            db,
                            [request.character_id, "user"],  # Generic user ID
                            metadata={"source": "dialogue_generation"}
                        )
                    except Exception as e:
                        print(f"Error creating conversation: {str(e)}")
                        conversation_id = "temp_conversation_" + str(hash(request.user_message))[:8]
                
                # Create message
                message = Message(
                    role="assistant",
                    content=response_text,
                    metadata={
                        "character": character_name,
                        "character_id": request.character_id,
                        "prompt_version_id": request.prompt_version_id
                    }
                )
                
                # Add message to conversation if we have a valid conversation_id
                if conversation_id and conversation_id != "temp_conversation_id":
                    try:
                        await self.add_message(db, conversation_id, message)
                        
                        # Create user message and add to conversation
                        user_message = Message(
                            role="user",
                            content=request.user_message,
                            metadata={}
                        )
                        await self.add_message(db, conversation_id, user_message)
                    except Exception as e:
                        print(f"Error adding messages to conversation: {str(e)}")
                
                # Create response object
                dialogue_response = DialogueResponse(
                    message=message,
                    conversation_id=conversation_id,
                    prompt_used={
                        "template": prompt_template,
                        "version_id": request.prompt_version_id or "default"
                    },
                    context_used={
                        "knowledge_chunks_used": [chunk.get("id", "") for chunk in knowledge_chunks if isinstance(chunk, dict) and "id" in chunk],
                    }
                )
                
                return dialogue_response
                
            except Exception as e:
                print(f"Error generating response: {str(e)}")
                # Create fallback response in case of error
                message = Message(
                    role="assistant",
                    content=f"I'm sorry, but I'm having trouble responding right now.",
                    metadata={
                        "error": str(e),
                        "character_id": request.character_id
                    }
                )
                
                return DialogueResponse(
                    message=message,
                    conversation_id=request.conversation_id or "error_conversation",
                    prompt_used={},
                    context_used={}
                )
                
        except Exception as e:
            print(f"Error in generate_dialogue: {str(e)}")
            # Create fallback response in case of error
            message = Message(
                role="assistant",
                content=f"I'm sorry, but I'm having trouble responding right now.",
                metadata={
                    "error": str(e),
                    "character_id": request.character_id
                }
            )
            
            return DialogueResponse(
                message=message,
                conversation_id=request.conversation_id or "error_conversation",
                prompt_used={},
                context_used={}
            )

# Create a singleton instance
dialogue_service = DialogueService() 