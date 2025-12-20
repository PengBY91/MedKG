from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

class DataAsset:
    """Data asset model for governance."""
    def __init__(
        self,
        name: str,
        tenant_id: str,
        asset_type: str,
        owner_id: str
    ):
        self.id = str(uuid.uuid4())
        self.tenant_id = tenant_id
        self.name = name
        self.type = asset_type  # dataset, table, field, document
        self.owner_id = owner_id
        self.steward_id = None  # Data steward
        self.description = ""
        self.quality_score = 0.0
        self.metadata = {}
        self.lineage = {"upstream": [], "downstream": []}
        self.tags = []
        self.status = "active"
        self.created_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()

class DataGovernanceService:
    """Data governance service for asset management and quality control."""
    
    def __init__(self):
        self.assets: Dict[str, DataAsset] = {}
        self.quality_rules = []
        
        # Create sample assets
        self._create_sample_assets()
    
    def _create_sample_assets(self):
        """Create sample data assets."""
        # Sample terminology dataset
        term_asset = DataAsset(
            name="医保术语标准库",
            tenant_id="default",
            asset_type="dataset",
            owner_id="admin"
        )
        term_asset.description = "包含所有标准化医保术语的主数据集"
        term_asset.quality_score = 0.95
        term_asset.metadata = {
            "row_count": 12500,
            "column_count": 8,
            "last_updated": "2024-12-19",
            "update_frequency": "daily"
        }
        term_asset.tags = ["terminology", "master_data", "high_quality"]
        self.assets[term_asset.id] = term_asset
        
        # Sample policy document
        policy_asset = DataAsset(
            name="2024年医保支付政策文档",
            tenant_id="default",
            asset_type="document",
            owner_id="admin"
        )
        policy_asset.description = "最新医保支付政策文档集合"
        policy_asset.quality_score = 0.88
        policy_asset.metadata = {
            "document_count": 156,
            "total_pages": 3420,
            "format": "PDF",
            "language": "zh-CN"
        }
        policy_asset.tags = ["policy", "regulation", "2024"]
        self.assets[policy_asset.id] = policy_asset
        
        # Sample rules dataset
        rules_asset = DataAsset(
            name="SHACL规则库",
            tenant_id="default",
            asset_type="dataset",
            owner_id="admin"
        )
        rules_asset.description = "编译后的SHACL规则集合"
        rules_asset.quality_score = 0.92
        rules_asset.metadata = {
            "rule_count": 245,
            "active_rules": 230,
            "last_validated": "2024-12-19"
        }
        rules_asset.tags = ["rules", "shacl", "validation"]
        rules_asset.lineage["upstream"] = [policy_asset.id]
        self.assets[rules_asset.id] = rules_asset
        
        # 4. Sample Provider Registry
        provider_asset = DataAsset(
            name="医疗机构注册目录",
            tenant_id="default",
            asset_type="dataset",
            owner_id="admin"
        )
        provider_asset.description = "全省定点医疗机构及其资质信息"
        provider_asset.quality_score = 0.98
        provider_asset.metadata = {
            "hospital_count": 1240,
            "clinic_count": 8500,
            "last_audit": "2024-11-30"
        }
        provider_asset.tags = ["provider", "hospital", "registry"]
        self.assets[provider_asset.id] = provider_asset
        
        # 5. Sample Claims Dataset
        claims_asset = DataAsset(
            name="2023年度结算清算数据",
            tenant_id="default",
            asset_type="dataset",
            owner_id="reviewer"
        )
        claims_asset.description = "2023年度所有医保结算和基金清算流水"
        claims_asset.quality_score = 0.75
        claims_asset.metadata = {
            "record_count": "54.2M",
            "total_amount": "12.5B",
            "anonymized": True
        }
        claims_asset.tags = ["claims", "financial", "historical"]
        self.assets[claims_asset.id] = claims_asset

    
    async def create_asset(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new data asset."""
        asset = DataAsset(
            name=asset_data["name"],
            tenant_id=asset_data.get("tenant_id", "default"),
            asset_type=asset_data["type"],
            owner_id=asset_data["owner_id"]
        )
        
        if "description" in asset_data:
            asset.description = asset_data["description"]
        if "metadata" in asset_data:
            asset.metadata = asset_data["metadata"]
        if "tags" in asset_data:
            asset.tags = asset_data["tags"]
        
        # Calculate initial quality score
        asset.quality_score = await self._calculate_quality_score(asset)
        
        self.assets[asset.id] = asset
        return self._asset_to_dict(asset)
    
    async def get_assets(
        self,
        tenant_id: str,
        asset_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get data assets with filtering."""
        assets = [a for a in self.assets.values() if a.tenant_id == tenant_id]
        
        if asset_type:
            assets = [a for a in assets if a.type == asset_type]
        
        # Sort by quality score descending
        assets.sort(key=lambda x: x.quality_score, reverse=True)
        
        # Pagination
        assets = assets[skip:skip + limit]
        
        return [self._asset_to_dict(a) for a in assets]
    
    async def get_asset(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """Get asset by ID."""
        asset = self.assets.get(asset_id)
        if not asset:
            return None
        return self._asset_to_dict(asset)
    
    async def update_asset(
        self,
        asset_id: str,
        asset_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update asset information."""
        asset = self.assets.get(asset_id)
        if not asset:
            return None
        
        if "name" in asset_data:
            asset.name = asset_data["name"]
        if "description" in asset_data:
            asset.description = asset_data["description"]
        if "metadata" in asset_data:
            asset.metadata.update(asset_data["metadata"])
        if "tags" in asset_data:
            asset.tags = asset_data["tags"]
        if "steward_id" in asset_data:
            asset.steward_id = asset_data["steward_id"]
        
        asset.updated_at = datetime.utcnow().isoformat()
        
        # Recalculate quality score
        asset.quality_score = await self._calculate_quality_score(asset)
        
        return self._asset_to_dict(asset)
    
    async def get_lineage(self, asset_id: str) -> Dict[str, Any]:
        """Get asset lineage (upstream and downstream)."""
        asset = self.assets.get(asset_id)
        if not asset:
            return {"error": "Asset not found"}
        
        # Build lineage graph
        lineage = {
            "asset": self._asset_to_dict(asset),
            "upstream": [
                self._asset_to_dict(self.assets[aid])
                for aid in asset.lineage["upstream"]
                if aid in self.assets
            ],
            "downstream": [
                self._asset_to_dict(self.assets[aid])
                for aid in asset.lineage["downstream"]
                if aid in self.assets
            ]
        }
        
        return lineage
    
    async def get_quality_report(self, tenant_id: str) -> Dict[str, Any]:
        """Get data quality report for tenant."""
        assets = [a for a in self.assets.values() if a.tenant_id == tenant_id]
        
        if not assets:
            return {
                "total_assets": 0,
                "average_quality": 0,
                "quality_distribution": {}
            }
        
        total_quality = sum(a.quality_score for a in assets)
        avg_quality = total_quality / len(assets)
        
        # Quality distribution
        distribution = {
            "excellent": len([a for a in assets if a.quality_score >= 0.9]),
            "good": len([a for a in assets if 0.7 <= a.quality_score < 0.9]),
            "fair": len([a for a in assets if 0.5 <= a.quality_score < 0.7]),
            "poor": len([a for a in assets if a.quality_score < 0.5])
        }
        
        return {
            "total_assets": len(assets),
            "average_quality": round(avg_quality, 2),
            "quality_distribution": distribution,
            "by_type": {
                "dataset": len([a for a in assets if a.type == "dataset"]),
                "document": len([a for a in assets if a.type == "document"]),
                "table": len([a for a in assets if a.type == "table"])
            }
        }
    
    async def _calculate_quality_score(self, asset: DataAsset) -> float:
        """Calculate quality score for asset."""
        score = 0.0
        
        # Completeness (40%)
        completeness = 0.0
        if asset.name:
            completeness += 0.25
        if asset.description:
            completeness += 0.25
        if asset.metadata:
            completeness += 0.25
        if asset.owner_id:
            completeness += 0.25
        score += completeness * 0.4
        
        # Freshness (30%)
        # Mock: assume recent updates are better
        score += 0.3
        
        # Consistency (30%)
        # Mock: assume tags and metadata indicate consistency
        if asset.tags:
            score += 0.15
        if asset.metadata:
            score += 0.15
        
        return min(score, 1.0)
    
    def _asset_to_dict(self, asset: DataAsset) -> Dict[str, Any]:
        """Convert asset to dict."""
        return {
            "id": asset.id,
            "tenant_id": asset.tenant_id,
            "name": asset.name,
            "type": asset.type,
            "owner_id": asset.owner_id,
            "steward_id": asset.steward_id,
            "description": asset.description,
            "quality_score": asset.quality_score,
            "metadata": asset.metadata,
            "lineage": asset.lineage,
            "tags": asset.tags,
            "status": asset.status,
            "created_at": asset.created_at,
            "updated_at": asset.updated_at
        }
