import asyncio
import openai
from typing import Dict, Any, List
from tenacity import retry, wait_random_exponential, stop_after_attempt, retry_if_exception_type

# Use relative import for config
from .config import Config

# Store conversation message history
conversation_history: Dict[str, List[Dict[str, Any]]] = {}

class PearlApiClient:
    """Client for interacting with Pearl API with conversation tracking"""
    
    def __init__(self, api_key: str, base_url: str = None):
        """
        Initialize the Pearl API client
        
        Args:
            api_key: Pearl API key
            base_url: Pearl API base URL (optional)
            
        Raises:
            ValueError: If api_key is not provided or is empty
        """
        if not api_key:
            raise ValueError("API key must be provided")
            
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url=base_url or Config.PEARL_API_BASE_URL
        )
    
    def format_messages_for_pearl(self, messages):
        """Format messages for Pearl API"""
        formatted_messages = []
        for message in messages:
            if isinstance(message, dict):
                formatted_messages.append(message)
            else:
                formatted_messages.append({
                    "role": message.role,
                    "content": message.content
                })
        return formatted_messages
    
    # Define a custom retry predicate
    def _is_422_error(self, exception):
        """Check if an exception represents a 422 status code"""
        status_code = getattr(exception, 'status_code', None)
        if hasattr(exception, 'response') and hasattr(exception.response, 'status_code'):
            status_code = exception.response.status_code
        return status_code == 422

    @retry(
        wait=wait_random_exponential(min=Config.MIN_RETRY_WAIT, max=Config.MAX_RETRY_WAIT),
        stop=stop_after_attempt(Config.MAX_RETRIES),
        retry=retry_if_exception_type(openai.UnprocessableEntityError)
    )
    async def call_api_with_retry(self, messages, session_id, mode):
        """
        Call Pearl API with retry logic - only retry on 422 status code (UnprocessableEntityError)
        
        Args:
            messages: List of message objects
            session_id: Session ID for the conversation
            mode: Pearl API mode
            is_retry: Whether this is a retry attempt
        """
        metadata = {
            "sessionId": session_id,
            "mode": mode
        }

        try:
            # Create a new client for each request to avoid connection issues
            client = openai.OpenAI(
                api_key=self.client.api_key,
                base_url=self.client.base_url
            )
            
            # Need to use sync client in async function
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.chat.completions.create(
                    model="pearl-ai",
                    messages=self.format_messages_for_pearl(messages),
                    metadata=metadata
                )
            )
            
            # Store the response in conversation history
            if session_id not in conversation_history:
                # Initialize with the user's messages first
                conversation_history[session_id] = messages.copy()
            
            # Add the assistant's response
            conversation_history[session_id].append({
                "role": "assistant",
                "content": response.choices[0].message.content
            })
            
            return response
        except openai.UnprocessableEntityError as e:
            # 422 error - expert verification in progress
            print(f"Expert verification in progress (422 status). Will retry.")
            raise  # Re-raise to allow tenacity to retry
        except Exception as e:
            # For any other errors, don't retry
            print(f"Error calling Pearl API: {e}")
            raise  # Non-422 errors won't be retried by tenacity
    
    def get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session
        
        Args:
            session_id: Session ID for the conversation
        """
        return conversation_history.get(session_id, [])
    
    def add_user_message(self, session_id: str, message: str) -> None:
        """
        Add a user message to the conversation history
        
        Args:
            session_id: Session ID for the conversation
            message: User message text
        """
        if session_id not in conversation_history:
            conversation_history[session_id] = []
        
        conversation_history[session_id].append({
            "role": "user",
            "content": message
        })
    
    def add_message(self, session_id: str, role: str, content: str) -> None:
        """
        Add a message to the conversation history with specified role
        
        Args:
            session_id: Session ID for the conversation
            role: Message role (user, assistant, system)
            content: Message content
        """
        if session_id not in conversation_history:
            conversation_history[session_id] = []
        
        conversation_history[session_id].append({
            "role": role,
            "content": content
        })