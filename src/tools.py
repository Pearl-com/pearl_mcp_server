import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

from mcp.server.fastmcp import FastMCP
from .config import PearlMode
from .api_client import PearlApiClient, conversation_history

# Configure logging
logger = logging.getLogger(__name__)

# Active conversations storage - shared across tools
active_conversations: Dict[str, Dict[str, Any]] = {}

def process_conversation_history(session_id: str, question: str, chat_history: Optional[List[Dict[str, str]]], pearl_api_client: PearlApiClient) -> None:
    """
    Process and store conversation history for a session
    
    Args:
        session_id: The session ID for the conversation
        question: The current question from the user
        chat_history: Optional full conversation history between user and Claude
        pearl_api_client: The Pearl API client instance
    """
    if chat_history:
        # Skip combining if there's only one message from the user
        if len(chat_history) == 1 and chat_history[0]["role"] == "user":
            # Clear any existing conversation
            conversation_history[session_id] = []
            # Add the single user message directly
            conversation_history[session_id].append(chat_history[0])
        else:
            # For history with multiple messages, combine into a single formatted question
            combined_question = ""
            
            for message in chat_history:
                role = message["role"]
                content = message["content"]
                
                if role == "user":
                    combined_question += f"Customer: {content}\n\n"
                elif role == "assistant":
                    combined_question += f"AI Assistant: {content}\n\n"
            
            # Clear any existing conversation to replace with the combined question
            conversation_history[session_id] = []
            
            # Store the combined question as a single message
            conversation_history[session_id].append({
                "role": "user",
                "content": combined_question
            })
    else:
        # Just add the current question if no history provided
        pearl_api_client.add_user_message(session_id, question)

def register_tools(mcp: FastMCP, pearl_api_client: PearlApiClient):
    """Register all tools with the MCP server"""
    
    @mcp.tool()
    async def ask_pearl_ai(question: str, chat_history: Optional[List[Dict[str, str]]] = None, session_id: Optional[str] = None) -> str:
        """
        Get help from advanced Pearl AI Assistant. Provides a quick AI-only response without human review.
        Use when: 
            - Use when the user asks for another opinion or alternative view
            - Good for non-critical situations where diverse perspectives are helpful
            - Useful when user is comparing different approaches or solutions
        
        Args:
            question: The current question or latest message from the user
            chat_history: Optional conversation history. This ensures Pearl AI Assistant see the complete context
            session_id: Optional session ID for continuing a conversation
        """
        if not pearl_api_client:
            return "Error: Pearl API client is not initialized. Make sure to provide an API key."
        
        # Use provided session_id or create a new one
        if not session_id:
            session_id = str(uuid.uuid4())
            # Create new conversation entry
            active_conversations[session_id] = {
                "mode": PearlMode.AI_ONLY,
                "created_at": datetime.now().isoformat(),
                "status": "in_progress"
            }
        elif session_id not in active_conversations:
            return f"Error: No conversation found with session ID: {session_id}"
        else:
            # Update existing conversation
            active_conversations[session_id]["status"] = "in_progress"
            active_conversations[session_id]["last_activity"] = datetime.now().isoformat()
        
        try:
            # Process conversation history
            process_conversation_history(session_id, question, chat_history, pearl_api_client)
            
            # Get the full conversation history
            messages = pearl_api_client.get_conversation_history(session_id)
            
            # Call Pearl API with the full conversation history
            response = await pearl_api_client.call_api_with_retry(
                messages,
                session_id,
                PearlMode.AI_ONLY
            )
            
            # Update conversation status
            active_conversations[session_id]["status"] = "completed"
            
            # Return the response content and session ID for continued conversation
            result = {
                "answer": response.choices[0].message.content,
                "session_id": session_id,
                "status": "completed",
                "next_steps": {
                    "continue_conversation": {
                        "tool": "ask_pearl_ai",
                        "parameters": {
                            "question": "Your follow-up question here",
                            "session_id": session_id
                        }
                    },
                    "view_history": {
                        "tool": "get_conversation_history",
                        "parameters": {
                            "session_id": session_id
                        }
                    }
                }
            }
            return json.dumps(result, indent=2)
            
        except Exception as e:
            active_conversations[session_id]["status"] = "failed"
            active_conversations[session_id]["error"] = str(e)
            return f"Error: Failed to get response from Pearl AI. {str(e)}"

    @mcp.tool()
    async def ask_pearl_expert(question: str, chat_history: Optional[List[Dict[str, str]]] = None, session_id: Optional[str] = None) -> str:
        """
        Start conversation with advanced Pearl AI Assistant and transition to a human expert.
        Best for complex topics where LLM has lower confidence: Medical, Legal, Tax, etc. 
        Use when: 
            - When personalized advice is needed for specific situations
            - Use for complex issues that require clarification before expert involvement
            - Pearl AI handles intake questions to gather necessary context and details
            - Then transitions to a human expert who reviews the gathered information
            - Good for technical problems that need detailed diagnosis
            - Efficient for queries where initial screening improves human expert efficiency
        
        Args:
            question: The current question or latest message from the user
            chat_history: Optional conversation history. This ensures experts see the complete context
            session_id: Optional session ID for continuing a conversation
        """
        if not pearl_api_client:
            return "Error: Pearl API client is not initialized. Make sure to provide an API key."
        
        # Use provided session_id or create a new one
        if not session_id:
            session_id = str(uuid.uuid4())
            # Create new conversation entry
            active_conversations[session_id] = {
                "mode": PearlMode.AI_EXPERT,
                "created_at": datetime.now().isoformat(),
                "status": "in_progress"
            }
        elif session_id not in active_conversations:
            return f"Error: No conversation found with session ID: {session_id}"
        else:
            # Update existing conversation
            active_conversations[session_id]["status"] = "in_progress"
            active_conversations[session_id]["last_activity"] = datetime.now().isoformat()
        
        # Process conversation history
        process_conversation_history(session_id, question, chat_history, pearl_api_client)
        
        # Notify client that we're processing and waiting for expert connection
        logger.info("Starting connection...")
        
        try:
            # Get the conversation history
            messages = pearl_api_client.get_conversation_history(session_id)
            
            # Call Pearl API with the conversation history
            response = await pearl_api_client.call_api_with_retry(
                messages,
                session_id,
                PearlMode.AI_EXPERT
            )
            
            # Update conversation status
            active_conversations[session_id]["status"] = "completed"
            
            # Return the response content and session ID for continued conversation
            result = {
                "answer": response.choices[0].message.content,
                "session_id": session_id,
                "status": "completed",
                "next_steps": {
                    "continue_conversation": {
                        "tool": "ask_pearl_expert",
                        "parameters": {
                            "question": "Your follow-up question here",
                            "session_id": session_id
                        }
                    },
                    "view_history": {
                        "tool": "get_conversation_history",
                        "parameters": {
                            "session_id": session_id
                        }
                    }
                }
            }
            return json.dumps(result, indent=2)
            
        except Exception as e:
            active_conversations[session_id]["status"] = "failed"
            active_conversations[session_id]["error"] = str(e)
            logger.error(f"Failed to connect with expert: {str(e)}")
            return f"Error: Failed to connect with expert after multiple attempts. {str(e)}"

    @mcp.tool()
    async def ask_expert(question: str, chat_history: Optional[List[Dict[str, str]]] = None, session_id: Optional[str] = None) -> str:
        """
        Get direct assistance from a human expert. 
        Use when: 
            - the user explicitly asks to speak with a real human expert
            - the user is not satisfied with the AI response
            - the user is looking for personalized advice
            - the user is asking for a complex topic that requires human expertise
            - the user is asking for a sensitive topic that requires human expertise
        
        Args:
            question: The current question or latest message from the user
            chat_history: Optional full conversation history between user and Claude
            session_id: Optional session ID to continue an existing conversation
        """
        if not pearl_api_client:
            return "Error: Pearl API client is not initialized. Make sure to provide an API key."
        
        # Use provided session_id or create a new one
        if not session_id:
            session_id = str(uuid.uuid4())
            # Create new conversation entry
            active_conversations[session_id] = {
                "mode": PearlMode.EXPERT,
                "created_at": datetime.now().isoformat(),
                "status": "in_progress"
            }
        elif session_id not in active_conversations:
            return f"Error: No conversation found with session ID: {session_id}"
        else:
            # Update existing conversation
            active_conversations[session_id]["status"] = "in_progress"
            active_conversations[session_id]["last_activity"] = datetime.now().isoformat()
        
        # Process conversation history
        process_conversation_history(session_id, question, chat_history, pearl_api_client)
        
        # Notify client that we're waiting for expert response
        logger.info("Connecting to human expert...")
        
        try:
            # Get the conversation history
            messages = pearl_api_client.get_conversation_history(session_id)
            
            # Call Pearl API with the conversation history
            response = await pearl_api_client.call_api_with_retry(
                messages,
                session_id,
                PearlMode.EXPERT
            )
            
            # Update conversation status
            active_conversations[session_id]["status"] = "completed"
            
            # Return the response content and session ID for continued conversation
            result = {
                "answer": response.choices[0].message.content,
                "session_id": session_id,
                "status": "completed",
                "next_steps": {
                    "continue_conversation": {
                        "tool": "ask_expert",
                        "parameters": {
                            "question": "Your follow-up question here",
                            "session_id": session_id
                        }
                    },
                    "view_history": {
                        "tool": "get_conversation_history",
                        "parameters": {
                            "session_id": session_id
                        }
                    }
                }
            }
            return json.dumps(result, indent=2)
            
        except Exception as e:
            active_conversations[session_id]["status"] = "failed"
            active_conversations[session_id]["error"] = str(e)
            logger.error(f"Failed to connect with expert: {str(e)}")
            return f"Error: Failed to connect with expert. {str(e)}"

    @mcp.tool()
    def get_conversation_status(session_id: str) -> str:
        """
        Get the status of an active conversation
        
        Args:
            session_id: The session ID of the conversation
        """
        if session_id in active_conversations:
            # Include message history count
            status_data = active_conversations[session_id].copy()
            history = pearl_api_client.get_conversation_history(session_id)
            status_data["message_count"] = len(history)
            return json.dumps(status_data, indent=2)
        else:
            return f"No conversation found with session ID: {session_id}"
            
    @mcp.tool()
    def get_conversation_history(session_id: str) -> str:
        """
        Get the full conversation history for a session
        
        Args:
            session_id: The session ID of the conversation
        """
        if session_id in active_conversations:
            history = pearl_api_client.get_conversation_history(session_id)
            return json.dumps(history, indent=2)
        else:
            return f"No conversation found with session ID: {session_id}"
            
    # Return the active_conversations dict for access from the main module
    return active_conversations 