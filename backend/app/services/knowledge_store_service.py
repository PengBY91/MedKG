import json
import os
from typing import List, Dict, Any, Optional
import uuid
from app.db.base import SessionLocal
from app.db.models import Rule as RuleModel, Terminology as TerminologyModel
from app.services.cache_service import cache_service, cached

class KnowledgeStoreService:
    def __init__(self):
        # We'll use database sessions instead of JSON files
        pass

    # --- Rules Management ---
    @cached("knowledge_rules", expire=3600)
    async def get_all_rules(self, tenant_id: str = "default") -> List[Dict]:
        db = SessionLocal()
        try:
            rules = db.query(RuleModel).filter(RuleModel.tenant_id == tenant_id).all()
            return [self._rule_to_dict(r) for r in rules]
        finally:
            db.close()

    async def add_rule(self, rule_data: Dict, tenant_id: str = "default"):
        db = SessionLocal()
        try:
            rule_id = rule_data.get("id") or str(uuid.uuid4())[:12]
            
            # Check for existing
            existing = db.query(RuleModel).filter(RuleModel.id == rule_id).first()
            
            if existing:
                # Update
                existing.name = rule_data.get("name") or rule_data.get("subject", "Unnamed Rule")
                existing.description = rule_data.get("description") or rule_data.get("explanation", "")
                existing.shacl_content = rule_data.get("shacl_content", "")
                existing.status = rule_data.get("status", "draft")
                existing.policy_id = rule_data.get("policy_id")
            else:
                # Create
                new_rule = RuleModel(
                    id=rule_id,
                    tenant_id=tenant_id,
                    name=rule_data.get("name") or rule_data.get("subject", "Unnamed Rule"),
                    description=rule_data.get("description") or rule_data.get("explanation", ""),
                    shacl_content=rule_data.get("shacl_content", ""),
                    status=rule_data.get("status", "draft"),
                    policy_id=rule_data.get("policy_id")
                )
                db.add(new_rule)
            
            db.commit()
            
            # Invalidate cache
            await cache_service.clear_pattern(f"knowledge_rules:{tenant_id}*")
            
            return rule_data
        finally:
            db.close()

    async def delete_rule(self, rule_id: str):
        db = SessionLocal()
        try:
            rule = db.query(RuleModel).filter(RuleModel.id == rule_id).first()
            if rule:
                tenant_id = rule.tenant_id
                db.delete(rule)
                db.commit()
                # Invalidate cache
                await cache_service.clear_pattern(f"knowledge_rules:{tenant_id}*")
        finally:
            db.close()

    # --- Terminology Management ---
    @cached("knowledge_terms", expire=3600)
    async def get_all_terms(self, tenant_id: str = "default") -> List[Dict]:
        db = SessionLocal()
        try:
            terms = db.query(TerminologyModel).filter(TerminologyModel.tenant_id == tenant_id).all()
            return [self._term_to_dict(t) for t in terms]
        finally:
            db.close()

    async def add_terms(self, terms_data: List[Dict], tenant_id: str = "default"):
        db = SessionLocal()
        try:
            for item in terms_data:
                term_text = item.get("term")
                if not term_text:
                    continue
                
                # Check for existing in this tenant
                existing = db.query(TerminologyModel).filter(
                    TerminologyModel.tenant_id == tenant_id,
                    TerminologyModel.raw_term == term_text
                ).first()
                
                if existing:
                    existing.standard_code = item.get("code")
                    existing.standard_name = item.get("standard_name")
                    existing.code_system = item.get("code_system") or "SNOMED-CT"
                    existing.confidence = item.get("confidence", 1.0)
                    existing.status = item.get("status", "approved")
                else:
                    new_term = TerminologyModel(
                        id=str(uuid.uuid4()),
                        tenant_id=tenant_id,
                        raw_term=term_text,
                        standard_code=item.get("code"),
                        standard_name=item.get("standard_name"),
                        code_system=item.get("code_system") or "SNOMED-CT",
                        confidence=item.get("confidence", 1.0),
                        status=item.get("status", "approved")
                    )
                    db.add(new_term)
            
            db.commit()
            
            # Invalidate cache
            await cache_service.clear_pattern(f"knowledge_terms:{tenant_id}*")
            
            return await self.get_all_terms(tenant_id)
        finally:
            db.close()

    async def delete_term(self, term_text: str, tenant_id: str = "default"):
        db = SessionLocal()
        try:
            db.query(TerminologyModel).filter(
                TerminologyModel.tenant_id == tenant_id,
                TerminologyModel.raw_term == term_text
            ).delete()
            db.commit()
            # Invalidate cache
            await cache_service.clear_pattern(f"knowledge_terms:{tenant_id}*")
        finally:
            db.close()

    def _rule_to_dict(self, rule: RuleModel) -> Dict:
        return {
            "id": rule.id,
            "name": rule.name,
            "description": rule.description,
            "shacl_content": rule.shacl_content,
            "status": rule.status,
            "policy_id": rule.policy_id,
            "created_at": rule.created_at.isoformat() if rule.created_at else None
        }

    def _term_to_dict(self, term: TerminologyModel) -> Dict:
        return {
            "term": term.raw_term,
            "code": term.standard_code,
            "standard_name": term.standard_name,
            "code_system": term.code_system,
            "confidence": term.confidence,
            "status": term.status
        }

# Singleton
knowledge_store = KnowledgeStoreService()
