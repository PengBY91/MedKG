import os
import logging
from typing import Optional, List, Dict, Any
from neo4j import AsyncGraphDatabase, AsyncDriver
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

from app.core.config import settings

class Neo4jService:
    """
    Core service for managing Neo4j connection.
    Singleton pattern for connection pooling.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Neo4jService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.uri = settings.NEO4J_URI
        self.user = settings.NEO4J_USER
        self.password = settings.NEO4J_PASSWORD
        self.driver: Optional[AsyncDriver] = None
        self._initialized = True
        
    async def initialize(self):
        """Initialize the driver connection."""
        if self.driver:
            return
            
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            await self.driver.verify_connectivity()
            logger.info("Neo4j Core Driver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j Core Driver: {e}")
            self.driver = None
            
    async def close(self):
        """Close the driver connection."""
        if self.driver:
            await self.driver.close()
            self.driver = None
            
    async def list_databases(self) -> List[str]:
        """List available databases (requires Neo4j v4+)."""
        if not self.driver:
            return []
        try:
            # System database is usually used for administration
            query = "SHOW DATABASES"
            # Execute on 'system' database if possible, or default
            # Note: SHOW DATABASES usually works on any if sufficient privs, best on system
            async with self.driver.session(database="system") as session:
                result = await session.run(query)
                records = await result.data()
                return [r['name'] for r in records]
        except Exception as e:
            logger.warning(f"Failed to list databases (might be insufficient permissions or old version): {e}")
            # Fallback to just default/configured if listing fails
            return ["neo4j"]

    async def execute_query(self, query: str, params: Dict[str, Any] = None, database: str = None) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query and return results as a list of dictionaries.
        Handles session management automatically.
        """
        if not self.driver:
            error_msg = f"Neo4j driver not initialized. PW={self.password}"
            logging.error(error_msg)
            # Raise exception to be visible in API response (as 500)
            raise Exception(error_msg)
            
        if params is None:
            params = {}
            
        try:
            # Use specific database if requested, else default
            session_kwargs = {"database": database} if database else {}
            
            async with self.driver.session(**session_kwargs) as session:
                result = await session.run(query, params)
                return await result.data()
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return []

# Global instance
neo4j_service = Neo4jService()
