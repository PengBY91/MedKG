import os
import shutil
from datetime import datetime
from typing import Optional, Tuple
from fastapi import UploadFile
import logging

logger = logging.getLogger(__name__)

class FileStorageService:
    """
    Local file system storage service.
    Structure: storage/uploads/{category}/{tenant_id}/{year}/{month}/{filename}
    """
    
    def __init__(self, base_dir: str = "storage/uploads"):
        self.base_dir = base_dir
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir, exist_ok=True)
            logger.info(f"Created base storage directory: {self.base_dir}")

    def _get_path(self, category: str, tenant_id: str, filename: str) -> str:
        """Generate nested path structure."""
        now = datetime.now()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        
        dir_path = os.path.join(self.base_dir, category, tenant_id, year, month)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            
        return os.path.join(dir_path, filename)

    async def save_file(self, file: UploadFile, category: str, tenant_id: str, prefix: str = "") -> str:
        """
        Save an uploaded file to the local file system.
        Returns the relative path from base_dir.
        """
        filename = f"{prefix}_{file.filename}" if prefix else file.filename
        full_path = self._get_path(category, tenant_id, filename)
        
        try:
            with open(full_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Return path relative to base_dir or project root?
            # Let's return the absolute path for now or path from root
            return os.path.relpath(full_path, os.getcwd())
        except Exception as e:
            logger.error(f"Failed to save file {filename}: {str(e)}")
            raise e

    def get_file_path(self, relative_path: str) -> Optional[str]:
        """Verify and return the full path of a file."""
        full_path = os.path.join(os.getcwd(), relative_path)
        if os.path.exists(full_path):
            return full_path
        return None

    def delete_file(self, relative_path: str) -> bool:
        """Delete a file from storage."""
        full_path = os.path.join(os.getcwd(), relative_path)
        try:
            if os.path.exists(full_path):
                os.remove(full_path)
                return True
        except Exception as e:
            logger.error(f"Failed to delete file {relative_path}: {str(e)}")
        return False

# Singleton instance
file_storage = FileStorageService()
