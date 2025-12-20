import json
import os
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.db.base import SessionLocal
from app.db.models import GovernanceTask as GovernanceTaskModel

# The ReviewTask class is replaced by GovernanceTaskModel

class GovernanceService:
    """
    Manages the Human-in-the-Loop Workflow.
    Core features:
    1. Triage: Route low-confidence items to review queue.
    2. Feedback Loop: Collect corrections for model fine-tuning.
    3. Syndication: Sync approved data to knowledge base.
    """

    def __init__(self):
        # We'll use database sessions instead of JSON files
        # Threshold for auto-approval
        self.AUTO_APPROVE_THRESHOLD = 0.95

    def _save_tasks(self):
        pass

    def _load_tasks(self):
        pass

    async def create_review_task(self, doc_id: str, extraction_result: Dict, task_type: str = "general") -> str:
        """
        Analyze extraction confidence and triage.
        """
        entities = extraction_result.get("entities", [])
        if not entities and task_type == "general":
            conf = 1.0 
        elif task_type in ["rule_review", "term_review"]:
            conf = 0.5 
        else:
            conf = sum([e.get("confidence", 0.8) for e in entities]) / len(entities) if entities else 0.8

        db = SessionLocal()
        try:
            task_id = str(uuid.uuid4())
            status = "pending"
            final_data = None
            
            if conf >= self.AUTO_APPROVE_THRESHOLD:
                status = "auto_approved"
                final_data = extraction_result
            
            new_task = GovernanceTaskModel(
                id=task_id,
                doc_id=doc_id,
                status=status,
                task_type=task_type,
                extracted_data=json.dumps(extraction_result),
                final_data=json.dumps(final_data) if final_data else None,
                confidence=conf
            )
            
            db.add(new_task)
            
            # If auto-approved, sync (mock)
            if status == "auto_approved":
                await self._sync_to_knowledge_store_from_model(new_task)
                
            db.commit()
            return task_id
        finally:
            db.close()

    async def get_pending_reviews(self) -> List[Dict]:
        """Get queue for manual review from database."""
        db = SessionLocal()
        try:
            tasks = db.query(GovernanceTaskModel).filter(GovernanceTaskModel.status == "pending").all()
            return [self._task_to_dict(t) for t in tasks]
        finally:
            db.close()

    async def submit_review(self, task_id: str, decision: str, corrected_data: Optional[Dict], reviewer: str):
        """
        Process human feedback via database.
        decision: approve, reject, correct
        """
        db = SessionLocal()
        try:
            task = db.query(GovernanceTaskModel).filter(GovernanceTaskModel.id == task_id).first()
            if not task:
                raise ValueError("Task not found")
            
            task.status = decision
            task.reviewer_id = reviewer
            
            if decision == "correct" and corrected_data:
                task.final_data = json.dumps(corrected_data)
                self._save_feedback_for_training(json.loads(task.extracted_data), corrected_data)
            elif decision == "approve":
                task.final_data = task.extracted_data
            
            if decision in ["approve", "correct"]:
                await self._sync_to_knowledge_store_from_model(task)
                
            db.commit()
            return task.status
        finally:
            db.close()

    async def _sync_to_knowledge_store_from_model(self, task: GovernanceTaskModel):
        """Sync approved model data to Knowledge Store."""
        from app.services.knowledge_store_service import knowledge_store
        
        extracted_data = json.loads(task.extracted_data) if task.extracted_data else {}
        final_data = json.loads(task.final_data) if task.final_data else {}
        data = final_data or extracted_data
        
        if task.task_type == "rule_review":
            rules = data.get("rules", [])
            for rule in rules:
                if rule.get("status") == "success":
                    await knowledge_store.add_rule(rule)
                    
        elif task.task_type == "term_review":
            entities = data.get("entities", [])
            terms_to_add = []
            for e in entities:
                terms_to_add.append({
                    "term": e.get("term") if isinstance(e, dict) else (e.term if hasattr(e, 'term') else str(e)),
                    "code": e.get("suggestion") if isinstance(e, dict) else (e.suggestion if hasattr(e, 'suggestion') else None),
                    "display": e.get("display") if isinstance(e, dict) else e.get("term") if isinstance(e, dict) else str(e),
                    "system": "SNOMED-CT",
                    "status": "APPROVED"
                })
            if terms_to_add:
                await knowledge_store.add_terms(terms_to_add)

    def _task_to_dict(self, task: GovernanceTaskModel) -> Dict:
        return {
            "id": task.id,
            "doc_id": task.doc_id,
            "status": task.status,
            "task_type": task.task_type,
            "extracted_data": json.loads(task.extracted_data) if task.extracted_data else {},
            "final_data": json.loads(task.final_data) if task.final_data else {},
            "confidence": task.confidence,
            "reviewer_id": task.reviewer_id,
            "feedback_notes": task.feedback_notes,
            "created_at": task.created_at.isoformat() if task.created_at else None
        }

    def _save_feedback_for_training(self, original: Dict, corrected: Dict):
        """Save pair for Future Fine-Tuning (DeepKE)."""
        print("Saving feedback for model improvement...")

# Singleton
governance_service = GovernanceService()
