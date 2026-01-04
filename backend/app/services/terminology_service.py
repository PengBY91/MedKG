from typing import List, Dict, Any, Optional
import logging
import os

logger = logging.getLogger(__name__)

class TerminologyService:
    """
    Medical Terminology Service.
    
    CONFIGURATION REQUIRED:
    This service requires external MedCT/MedLink API access.
    Please configure the following environment variables:
    
    - MEDCT_API_URL: MedCT API endpoint
    - MEDCT_API_KEY: MedCT API key
    - MEDLINK_API_URL: MedLink API endpoint  
    - MEDLINK_API_KEY: MedLink API key
    
    If these are not configured, the service will raise errors.
    """
    
    def __init__(self):
        """Initialize with external API configuration."""
        self.medct_url = os.getenv("MEDCT_API_URL")
        self.medct_key = os.getenv("MEDCT_API_KEY")
        self.medlink_url = os.getenv("MEDLINK_API_URL")
        self.medlink_key = os.getenv("MEDLINK_API_KEY")
        
        if not all([self.medct_url, self.medct_key]):
            logger.warning("MedCT API not configured. Set MEDCT_API_URL and MEDCT_API_KEY environment variables.")
        
        if not all([self.medlink_url, self.medlink_key]):
            logger.warning("MedLink API not configured. Set MEDLINK_API_URL and MEDLINK_API_KEY environment variables.")
    
    async def search_concept(self, term: str, system: str = "SNOMED") -> List[Dict[str, Any]]:
        """
        Search for medical concept in terminology system.
        
        Args:
            term: Search term
            system: Terminology system (SNOMED, ICD-10, etc.)
        
        Returns:
            List of matching concepts
        
        Raises:
            RuntimeError: If API is not configured
        """
        if not self.medct_url or not self.medct_key:
            raise RuntimeError(
                "MedCT API not configured. Please set MEDCT_API_URL and MEDCT_API_KEY environment variables. "
                "See backend/app/services/terminology_service.py for details."
            )
        
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.medct_url}/search",
                    params={"term": term, "system": system},
                    headers={"Authorization": f"Bearer {self.medct_key}"}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"MedCT API error: {e}")
            raise
    
    async def get_concept_details(self, code: str, system: str = "SNOMED") -> Optional[Dict[str, Any]]:
        """Get detailed information about a medical concept."""
        if not self.medct_url or not self.medct_key:
            raise RuntimeError("MedCT API not configured")
        
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.medct_url}/concept/{code}",
                    params={"system": system},
                    headers={"Authorization": f"Bearer {self.medct_key}"}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"MedCT API error: {e}")
            return None
    
    async def get_relationships(self, code: str, relationship_type: str = None) -> List[Dict[str, Any]]:
        """Get relationships for a medical concept."""
        if not self.medlink_url or not self.medlink_key:
            raise RuntimeError(
                "MedLink API not configured. Please set MEDLINK_API_URL and MEDLINK_API_KEY environment variables."
            )
        
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                params = {"code": code}
                if relationship_type:
                    params["type"] = relationship_type
                
                response = await client.get(
                    f"{self.medlink_url}/relationships",
                    params=params,
                    headers={"Authorization": f"Bearer {self.medlink_key}"}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"MedLink API error: {e}")
            return []

# Singleton instance
terminology_service = TerminologyService()
