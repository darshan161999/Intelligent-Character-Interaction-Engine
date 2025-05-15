#!/usr/bin/env python
"""
Script to perform detailed analysis of a single RAG query
"""
import requests
import json
import time
from pprint import pprint
import os
import re

# Base URL for the API
BASE_URL = "http://localhost:8000/api"

# The specific query we want to analyze in detail
QUERY = {
    "character_id": "character_iron_man",
    "query": "Explain how your heart condition affected the development of your technology",
    "expected_response": "My heart condition led to the development of the Arc Reactor technology, which not only kept me alive but became a cornerstone of my Iron Man suits."
}

# Hardcoded character info since we don't have a direct endpoint
CHARACTER_INFO = {
    "character_iron_man": {
        "name": "Iron Man",
        "description": "Genius inventor, billionaire, and superhero who created a powered suit of armor to save his life and now uses his technology to protect the world as Iron Man.",
        "personality": "Confident, witty, and intelligent with a touch of arrogance. Known for sarcastic humor and quick thinking in difficult situations."
    }
}

def print_section(title):
    """Print a section title"""
    print("\n" + "="*100)
    print(f"  {title}")
    print("="*100 + "\n")

def check_server_connection():
    """Check if the server is running and accessible"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and accessible!")
            return True
    except requests.exceptions.ConnectionError:
        print("❌ Server not accessible. Please ensure the server is running with 'python main.py'.")
        return False
    
    return False

def get_character_info(character_id):
    """Get character information from hardcoded data"""
    print_section(f"GETTING CHARACTER INFO: {character_id}")
    
    if character_id in CHARACTER_INFO:
        character_info = CHARACTER_INFO[character_id]
        print("✅ Character info retrieved successfully")
        print(f"Name: {character_info.get('name', 'Unknown')}")
        print(f"Description: {character_info.get('description', 'No description')[:100]}...")
        print(f"Personality: {character_info.get('personality', 'No personality')[:100]}...")
        return character_info
    else:
        print(f"❌ Character info not found for: {character_id}")
        return None

def get_knowledge_chunks(query, character_id):
    """Get knowledge chunks for a query directly from the knowledge service"""
    print_section(f"RETRIEVING KNOWLEDGE CHUNKS")
    
    try:
        # Create a search request to directly query the knowledge service
        search_request = {
            "query": query,
            "top_k": 5,
            "filter_metadata": {
                "character": character_id.replace("character_", "").replace("_", " ").title()
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/knowledge/search",
            json=search_request,
            timeout=30
        )
        
        if response.status_code == 200:
            chunks = response.json()
            print(f"✅ Retrieved {len(chunks)} knowledge chunks")
            
            for i, chunk in enumerate(chunks):
                print(f"\nCHUNK {i+1}:")
                print(f"Content: {chunk['content']}")
                print(f"Source: {chunk.get('metadata', {}).get('source', 'Unknown')}")
                print(f"Similarity Score: {chunk.get('score', 'N/A')}")
            
            return chunks
        else:
            print(f"❌ Failed to retrieve knowledge chunks: {response.status_code}")
            print(f"Error: {response.text}")
            return []
    except Exception as e:
        print(f"❌ Error retrieving knowledge chunks: {str(e)}")
        return []

def reconstruct_prompt(character_info, chunks, query):
    """Reconstruct the prompt that would be sent to the LLM"""
    print_section(f"RECONSTRUCTING LLM PROMPT")
    
    # Get character information
    character_name = character_info.get("name", "Character")
    character_description = character_info.get("description", "A fictional character")
    character_personality = character_info.get("personality", "Friendly and helpful")
    
    # Format knowledge chunks
    knowledge_text = "RELEVANT KNOWLEDGE CHUNKS (USE ONLY THIS INFORMATION):\n\n"
    for i, chunk in enumerate(chunks):
        content = chunk.get('content', 'No content available')
        source = chunk.get('metadata', {}).get('source', 'Unknown source')
        score = chunk.get('score', 'N/A')
        knowledge_text += f"CHUNK {i+1}: {content}\nSource: {source}\nRelevance Score: {score}\n\n"
    
    # Construct the prompt based on the template in langgraph_orchestration.py
    prompt = f"""You are {character_name}, {character_description}.
Respond in character with the personality: {character_personality}.

EXTREMELY IMPORTANT INSTRUCTIONS:
1. You MUST ONLY use the knowledge provided below to answer the user's question.
2. If the knowledge doesn't contain information to answer the question, say "I don't have specific information about that in my knowledge base."
3. DO NOT use your pre-trained knowledge to answer questions about the character or their universe.
4. ONLY respond based on the knowledge context provided.
5. DO NOT MAKE UP ANY INFORMATION that is not explicitly provided in the knowledge context.
6. If you're unsure about something, say you don't have that information rather than guessing.

KNOWLEDGE CONTEXT:
{knowledge_text}

User: {query}
{character_name}:"""
    
    print(prompt)
    
    # Save the prompt to a file for later analysis
    with open("detailed_prompt.txt", "w", encoding="utf-8") as f:
        f.write(prompt)
    
    print("\n✅ Prompt saved to detailed_prompt.txt")
    
    return prompt

def generate_response(character_id, query):
    """Generate a response using the dialogue API"""
    print_section(f"GENERATING RESPONSE")
    
    request_data = {
        "character_id": character_id,
        "user_message": query,
        "context": {
            "location": "Avengers Tower",
            "situation": "Detailed Analysis"
        }
    }
    
    try:
        # Generate dialogue using LangGraph
        print("Calling dialogue generation API...")
        response = requests.post(
            f"{BASE_URL}/dialogue/generate-with-langgraph",
            json=request_data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            generated_response = result["message"]["content"]
            knowledge_chunk_ids = result["context_used"].get("knowledge_chunks_used", [])
            
            print("\n✅ Dialogue generation successful!")
            print(f"\nQuery: {query}")
            print(f"Response: \"{generated_response}\"\n")
            print(f"Knowledge chunks used: {len(knowledge_chunk_ids)}")
            print(f"Chunk IDs: {knowledge_chunk_ids}")
            
            # Get the actual chunks used
            print("\nRetrieving the actual chunks used:")
            retrieved_chunks = []
            for chunk_id in knowledge_chunk_ids:
                try:
                    chunk_response = requests.get(
                        f"{BASE_URL}/knowledge/chunks/{chunk_id}",
                        timeout=10
                    )
                    if chunk_response.status_code == 200:
                        chunk = chunk_response.json()
                        retrieved_chunks.append(chunk)
                        print(f"- Chunk {chunk_id}: {chunk['content'][:100]}...")
                except Exception as e:
                    print(f"Error retrieving chunk {chunk_id}: {str(e)}")
            
            # Add the retrieved chunks to the result
            result["retrieved_chunks"] = retrieved_chunks
            
            return result
        else:
            print(f"❌ Failed to generate dialogue: {response.status_code}")
            print(f"Error: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error generating dialogue: {str(e)}")
        return None

def evaluate_response(query, chunks, generated_response, expected_response):
    """Evaluate the response using the RAG metrics API"""
    print_section(f"EVALUATING RESPONSE")
    
    evaluation_data = {
        "query": query,
        "retrieved_chunks": chunks,
        "generated_response": generated_response,
        "expected_response": expected_response
    }
    
    try:
        print("Calling RAG evaluation API...")
        eval_response = requests.post(
            f"{BASE_URL}/evaluation/rag-metrics",
            json=evaluation_data,
            timeout=60
        )
        
        if eval_response.status_code == 200:
            eval_result = eval_response.json()
            
            print("\n✅ RAG evaluation successful!")
            print("\nEvaluation Metrics:")
            print(f"- Contextual Precision: {eval_result['metrics']['contextual_precision']:.4f}")
            print(f"- Contextual Recall: {eval_result['metrics']['contextual_recall']:.4f}")
            print(f"- Contextual Relevancy: {eval_result['metrics']['contextual_relevancy']:.4f}")
            print(f"- Combined Score: {eval_result['metrics']['combined_score']:.4f}")
            
            # Save the evaluation results to a file
            with open("detailed_evaluation.json", "w") as f:
                json.dump(eval_result, f, indent=2)
            
            print("\n✅ Evaluation results saved to detailed_evaluation.json")
            
            return eval_result
        else:
            print(f"❌ Failed to evaluate response: {eval_response.status_code}")
            print(f"Error: {eval_response.text}")
            return None
    except Exception as e:
        print(f"❌ Error evaluating response: {str(e)}")
        return None

def analyze_response_vs_chunks(response, chunks):
    """Analyze how the response uses information from the chunks"""
    print_section(f"ANALYZING RESPONSE AGAINST KNOWLEDGE CHUNKS")
    
    # Extract sentences from the response
    response_sentences = re.split(r'[.!?]+', response)
    response_sentences = [s.strip() for s in response_sentences if s.strip()]
    
    print("Response broken into sentences:")
    for i, sentence in enumerate(response_sentences):
        print(f"{i+1}. {sentence}")
    
    print("\nChecking for information from chunks in the response:")
    for i, chunk in enumerate(chunks):
        chunk_content = chunk.get('content', '')
        chunk_words = set(re.findall(r'\b\w+\b', chunk_content.lower()))
        
        # Find sentences that might be using this chunk
        for j, sentence in enumerate(response_sentences):
            sentence_words = set(re.findall(r'\b\w+\b', sentence.lower()))
            common_words = chunk_words.intersection(sentence_words)
            
            # If there are significant common words, highlight the connection
            if len(common_words) >= 3:
                print(f"\nPossible connection between Chunk {i+1} and Sentence {j+1}:")
                print(f"Chunk: {chunk_content[:100]}...")
                print(f"Sentence: {sentence}")
                print(f"Common words: {', '.join(common_words)}")

def save_complete_analysis(character_info, chunks, prompt, response_result, evaluation_result):
    """Save the complete analysis to a file"""
    print_section(f"SAVING COMPLETE ANALYSIS")
    
    analysis = {
        "query": QUERY,
        "character_info": character_info,
        "knowledge_chunks": chunks,
        "prompt": prompt,
        "response_result": response_result,
        "evaluation_result": evaluation_result
    }
    
    with open("detailed_query_analysis.json", "w") as f:
        json.dump(analysis, f, indent=2)
    
    print("✅ Complete analysis saved to detailed_query_analysis.json")

def create_analysis_markdown():
    """Create a markdown file with the analysis results"""
    print_section(f"CREATING ANALYSIS MARKDOWN")
    
    try:
        # Load the complete analysis
        with open("detailed_query_analysis.json", "r") as f:
            analysis = json.load(f)
        
        # Create markdown content
        markdown = f"""# Detailed RAG Query Analysis

## Query Information
- **Character**: {analysis["character_info"]["name"]}
- **Query**: "{analysis["query"]["query"]}"
- **Expected Response**: "{analysis["query"]["expected_response"]}"

## Knowledge Chunks Retrieved
The system retrieved the following knowledge chunks:

"""
        # Add knowledge chunks
        for i, chunk in enumerate(analysis["knowledge_chunks"]):
            markdown += f"""### Chunk {i+1}
- **Content**: {chunk.get('content', 'No content')}
- **Source**: {chunk.get('metadata', {}).get('source', 'Unknown')}
- **Similarity Score**: {chunk.get('score', 'N/A')}

"""

        # Add prompt
        markdown += f"""## Prompt Sent to LLM
```
{analysis["prompt"]}
```

## Generated Response
"{analysis["response_result"]["message"]["content"]}"

## Chunks Actually Used in Response
The following chunks were actually used in generating the response:

"""
        # Add chunks used
        if "retrieved_chunks" in analysis["response_result"]:
            for i, chunk in enumerate(analysis["response_result"]["retrieved_chunks"]):
                markdown += f"""### Used Chunk {i+1}
- **Content**: {chunk.get('content', 'No content')}
- **Source**: {chunk.get('source', 'Unknown')}
- **ID**: {chunk.get('id', 'Unknown')}

"""
        
        # Add evaluation metrics
        markdown += f"""## Evaluation Metrics
- **Contextual Precision**: {analysis["evaluation_result"]["metrics"]["contextual_precision"]:.4f}
- **Contextual Recall**: {analysis["evaluation_result"]["metrics"]["contextual_recall"]:.4f}
- **Contextual Relevancy**: {analysis["evaluation_result"]["metrics"]["contextual_relevancy"]:.4f}
- **Combined Score**: {analysis["evaluation_result"]["metrics"]["combined_score"]:.4f}

## Analysis Summary
This analysis demonstrates the RAG process from knowledge retrieval to response generation and evaluation. 
The system retrieved relevant chunks about Iron Man's heart condition and technology development, 
constructed a prompt with these chunks, and generated a response that utilized the provided knowledge.

The evaluation metrics show how well the system performed in terms of retrieving relevant information (precision), 
aligning with the expected response (recall), and effectively using the retrieved information in the generated response (relevancy).
"""
        
        # Save markdown file
        with open("detailed_query_analysis.md", "w", encoding="utf-8") as f:
            f.write(markdown)
        
        print("✅ Analysis markdown saved to detailed_query_analysis.md")
        
    except Exception as e:
        print(f"❌ Error creating analysis markdown: {str(e)}")

def run_detailed_analysis():
    """Run a detailed analysis of a single query"""
    print_section("STARTING DETAILED QUERY ANALYSIS")
    
    # Check if server is running
    if not check_server_connection():
        print("\n❌ Cannot proceed with analysis as the server is not accessible.")
        print("Please start the server with 'python main.py' and try again.")
        return
    
    # Get character info
    character_info = get_character_info(QUERY["character_id"])
    if not character_info:
        return
    
    # Get knowledge chunks
    chunks = get_knowledge_chunks(QUERY["query"], QUERY["character_id"])
    if not chunks:
        return
    
    # Reconstruct prompt
    prompt = reconstruct_prompt(character_info, chunks, QUERY["query"])
    
    # Generate response
    response_result = generate_response(QUERY["character_id"], QUERY["query"])
    if not response_result:
        return
    
    # Evaluate response
    evaluation_result = evaluate_response(
        QUERY["query"], 
        chunks, 
        response_result["message"]["content"], 
        QUERY["expected_response"]
    )
    if not evaluation_result:
        return
    
    # Analyze response against chunks
    analyze_response_vs_chunks(response_result["message"]["content"], chunks)
    
    # Save complete analysis
    save_complete_analysis(character_info, chunks, prompt, response_result, evaluation_result)
    
    # Create analysis markdown
    create_analysis_markdown()
    
    print_section("ANALYSIS COMPLETE")
    print("The detailed analysis has been saved to the following files:")
    print("- detailed_prompt.txt: The reconstructed prompt sent to the LLM")
    print("- detailed_evaluation.json: The evaluation metrics and results")
    print("- detailed_query_analysis.json: The complete analysis data")
    print("- detailed_query_analysis.md: A human-readable markdown summary of the analysis")

if __name__ == "__main__":
    run_detailed_analysis() 