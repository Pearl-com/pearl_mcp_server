import os
from dotenv import load_dotenv
from enum import Enum
from typing import Optional

# Load environment variables from .env file
load_dotenv()

# Pearl API modes
class PearlMode(str, Enum):
    AI_ONLY = "pearl-ai"
    AI_EXPERT = "pearl-ai-expert"
    EXPERT = "expert"

class Config:
    """Configuration class for Pearl MCP Server"""
    
    # Default values
    PEARL_API_BASE_URL = "https://api.pearl.com/api/v1/"
    MAX_RETRIES = 10
    MIN_RETRY_WAIT = 1
    MAX_RETRY_WAIT = 60
    
    # API key to be set at runtime
    PEARL_API_KEY: Optional[str] = os.getenv("PEARL_API_KEY")

    @classmethod
    def initialize(cls, api_key: str):
        """
        Initialize configuration with provided api key
        
        Args:
            api_key: Pearl API key
        """
        cls.PEARL_API_KEY = api_key