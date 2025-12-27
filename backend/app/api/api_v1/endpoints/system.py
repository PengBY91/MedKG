from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
import logging
from app.core.llm import llm_service
from app.core.kg import neo4j_service

router = APIRouter()
logger = logging.getLogger(__name__)

class LLMConfig(BaseModel):
    api_key: str
    base_url: str
    model: str

class KGConfig(BaseModel):
    uri: str
    user: str
    password: Optional[str] = None # Optional for update (if not changed)

@router.get("/config/llm")
async def get_llm_config():
    """Get current LLM configuration."""
    return {
        "success": True,
        "config": llm_service.get_config()
    }

@router.post("/config/llm")
async def update_llm_config(config: LLMConfig):
    """Update LLM configuration."""
    # Runtime update
    success = llm_service.reconfigure(config.api_key, config.base_url, config.model)
    
    # Persistence (write to .env)
    _update_env_file({
        "OPENAI_API_KEY": config.api_key,
        "OPENAI_BASE_URL": config.base_url,
        "OPENAI_MODEL": config.model
    })
    
    if not success:
         raise HTTPException(status_code=500, detail="Failed to initialize LLM client with provided credentials")
         
    return {"success": True, "message": "LLM configuration updated"}

@router.post("/test/llm")
async def test_llm_connection():
    """Test LLM connection."""
    client = llm_service.get_client()
    if not client:
        return {"success": False, "message": "Client not initialized"}
        
    try:
        # Simple test call
        await client.chat.completions.create(
            model=llm_service.get_model_name(),
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5
        )
        return {"success": True, "message": "Connection successful"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.get("/config/kg")
async def get_kg_config():
    """Get current KG configuration."""
    # Return current env values, mask password
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    
    return {
        "success": True,
        "config": {
            "uri": uri,
            "user": user,
            "password": "***" # Always mask
        }
    }

@router.post("/config/kg")
async def update_kg_config(config: KGConfig):
    """Update KG configuration."""
    # Update env vars
    os.environ["NEO4J_URI"] = config.uri
    os.environ["NEO4J_USER"] = config.user
    if config.password:
        os.environ["NEO4J_PASSWORD"] = config.password
        
    # Re-initialize service
    # Trigger re-init by removing old driver (requires accessing internal service logic or adding reinit method)
    # Since Neo4jService is singleton and `initialize` checks `_initialized`, we need a `reconfigure` method there too.
    # For now, we'll just close and nullify, next request will re-init? No, existing `initialize` guard blocks it.
    # We should add `reconfigure` to Neo4jService. Ideally.
    # Hack for now: update .env and require restart, OR update runtime and force re-init.
    
    # Let's handle persistence first
    env_updates = {
        "NEO4J_URI": config.uri,
        "NEO4J_USER": config.user
    }
    if config.password:
        env_updates["NEO4J_PASSWORD"] = config.password
        
    _update_env_file(env_updates)
    
    return {"success": True, "message": "KG configuration saved. Please restart service to apply (or implement runtime re-init)."}

@router.post("/test/kg")
async def test_kg_connection(config: Optional[KGConfig] = None):
    """Test KG connection (using current or provided config)."""
    # If config provided, try connecting with it without saving
    if config:
        from neo4j import GraphDatabase
        try:
            # Sync driver for quick test? Or async?
            # Creating a ad-hoc driver
            # Note: This blocks event loop if sync. Use Async.
            from neo4j import AsyncGraphDatabase
            auth = (config.user, config.password) if config.password else (os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
            driver = AsyncGraphDatabase.driver(config.uri, auth=auth)
            await driver.verify_connectivity()
            await driver.close()
            return {"success": True, "message": "Connection successful"}
        except Exception as e:
            return {"success": False, "message": str(e)}
            
    # Otherwise test current service
    if not neo4j_service.driver:
         return {"success": False, "message": "Service not initialized"}
    
    try:
        await neo4j_service.driver.verify_connectivity()
        return {"success": True, "message": "Connection active"}
    except Exception as e:
        return {"success": False, "message": str(e)}

def _update_env_file(updates: Dict[str, str]):
    """Helper to update .env file."""
    try:
        env_path = ".env"
        lines = []
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                lines = f.readlines()
        
        final_lines = []
        processed_keys = set()
        
        for line in lines:
            key = line.split("=")[0].strip()
            if key in updates:
                final_lines.append(f"{key}={updates[key]}\n")
                processed_keys.add(key)
            else:
                final_lines.append(line)
        
        for key, val in updates.items():
            if key not in processed_keys:
                if final_lines and not final_lines[-1].endswith("\n"):
                    final_lines.append("\n")
                final_lines.append(f"{key}={val}\n")
                
        with open(env_path, "w") as f:
            f.writelines(final_lines)
            
    except Exception as e:
        logger.error(f"Failed to write .env: {e}")
