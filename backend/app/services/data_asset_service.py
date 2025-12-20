import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.db.base import SessionLocal
from app.db.models import DataAsset as DataAssetModel

class DataAssetService:
    """
    Manages medical data assets (tables, views, files) and their metadata.
    """
    
    async def get_assets(
        self,
        tenant_id: str,
        asset_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            query = db.query(DataAssetModel).filter(DataAssetModel.tenant_id == tenant_id)
            if asset_type:
                query = query.filter(DataAssetModel.type == asset_type)
            
            assets = query.offset(skip).limit(limit).all()
            return [self._asset_to_dict(a) for a in assets]
        finally:
            db.close()

    async def get_asset(self, asset_id: str) -> Optional[Dict[str, Any]]:
        db = SessionLocal()
        try:
            asset = db.query(DataAssetModel).filter(DataAssetModel.id == asset_id).first()
            return self._asset_to_dict(asset) if asset else None
        finally:
            db.close()

    async def create_asset(self, asset_data: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            asset_id = str(uuid.uuid4())
            new_asset = DataAssetModel(
                id=asset_id,
                tenant_id=tenant_id,
                name=asset_data["name"],
                type=asset_data.get("type", "table"),
                description=asset_data.get("description", ""),
                schema_info=json.dumps(asset_data.get("schema", {})),
                quality_score=asset_data.get("quality_score", 0.0),
                owner=asset_data.get("owner", "system"),
                tags=json.dumps(asset_data.get("tags", []))
            )
            db.add(new_asset)
            db.commit()
            db.refresh(new_asset)
            return self._asset_to_dict(new_asset)
        finally:
            db.close()

    async def update_asset_quality(self, asset_id: str, score: float):
        db = SessionLocal()
        try:
            asset = db.query(DataAssetModel).filter(DataAssetModel.id == asset_id).first()
            if asset:
                asset.quality_score = score
                db.commit()
                return True
            return False
        finally:
            db.close()

    def _asset_to_dict(self, asset: DataAssetModel) -> Dict[str, Any]:
        return {
            "id": asset.id,
            "tenant_id": asset.tenant_id,
            "name": asset.name,
            "type": asset.type,
            "description": asset.description,
            "schema": json.loads(asset.schema_info) if asset.schema_info else {},
            "quality_score": asset.quality_score,
            "owner": asset.owner,
            "tags": json.loads(asset.tags) if asset.tags else [],
            "created_at": asset.created_at.isoformat() if asset.created_at else None,
            "updated_at": asset.updated_at.isoformat() if asset.updated_at else None
        }

# Singleton
data_asset_service = DataAssetService()
