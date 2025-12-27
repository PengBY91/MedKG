import os
import logging
from typing import Optional, Dict
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Ensure env vars are loaded
load_dotenv()

logger = logging.getLogger(__name__)

class LLMService:
    """
    Core service for managing OpenAI LLM client.
    Singleton pattern to ensure global access to the configured client.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.client: Optional[AsyncOpenAI] = None
        self.model: str = "gpt-4"
        self._init_client()
        self._initialized = True
        
    def _init_client(self):
        """Initialize client from environment variables."""
        api_key = os.getenv("OPENAI_API_KEY", "")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4")
        
        if api_key:
            try:
                self.client = AsyncOpenAI(
                    api_key=api_key,
                    base_url=base_url
                )
                logger.info(f"OpenAI Core Client initialized with base_url={base_url}, model={self.model}")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI Core Client: {e}")
                self.client = None
        else:
            logger.warning("OPENAI_API_KEY not set in Core LLMService.")
            self.client = None
            
    def get_client(self) -> Optional[AsyncOpenAI]:
        """Get the active OpenAI client."""
        return self.client
        
    def get_model_name(self) -> str:
        """Get the configured model name."""
        return self.model
        
    def get_config(self) -> Dict[str, str]:
        """Get current configuration (safely masked)."""
        key = os.getenv("OPENAI_API_KEY", "")
        masked_key = f"{key[:3]}...{key[-4:]}" if len(key) > 8 else "Not Set"
        
        return {
            "api_key": masked_key,
            "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            "model": os.getenv("OPENAI_MODEL", "gpt-4")
        }
        
    def reconfigure(self, api_key: str, base_url: str, model: str) -> bool:
        """
        Update environment variables and re-initialize client.
        Note: This updates the process environment, consistent with previous behavior.
        """
        os.environ["OPENAI_API_KEY"] = api_key
        os.environ["OPENAI_BASE_URL"] = base_url
        os.environ["OPENAI_MODEL"] = model
        
        self._init_client()
        return self.client is not None

# Global instance
llm_service = LLMService()
