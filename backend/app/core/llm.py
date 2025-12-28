import os
import logging
from typing import Optional, Dict
from openai import AsyncOpenAI
from dotenv import load_dotenv
from pathlib import Path

# Ensure env vars are loaded from backend/.env
# Get the backend directory (3 levels up from this file)
backend_dir = Path(__file__).parent.parent.parent
env_path = backend_dir / ".env"

# Load environment variables
if env_path.exists():
    load_dotenv(env_path)
    print(f"✓ Loaded .env from: {env_path}")
else:
    load_dotenv()  # Fallback to default search
    print(f"⚠ .env not found at {env_path}, using default search")

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
    
    async def generate_stream(self, prompt: str, temperature: float = 0.7):
        """
        Generate streaming response from LLM.
        Yields chunks of text as they are generated.
        """
        if not self.client:
            raise ValueError("LLM client not initialized")
        
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0 and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Streaming generation failed: {e}")
            raise

# Global instance
llm_service = LLMService()
