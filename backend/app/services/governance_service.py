import json
import os
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

class ReviewTask:
    def __init__(self, doc_id: str, extracted_data: Dict, confidence: float, task_type: str = "general"):
        self.id = str(uuid.uuid4())
        self.doc_id = doc_id
        self.status = "pending"  # pending, approved, rejected, corrected
        self.extracted_data = extracted_data
        self.final_data = None
        self.confidence = confidence
        self.task_type = task_type
        self.created_at = datetime.utcnow().isoformat()
        self.reviewer_id = None
        self.feedback_notes = None

    def to_dict(self):
        return vars(self)

    @staticmethod
    def from_dict(data):
        task = ReviewTask("", {}, 0)
        for k, v in data.items():
            setattr(task, k, v)
        return task

class GovernanceService:
    """
    Manages the Human-in-the-Loop Workflow.
    Core features:
    1. Triage: Route low-confidence items to review queue.
    2. Feedback Loop: Collect corrections for model fine-tuning.
    3. Syndication: Sync approved data to knowledge base.
    """

    def __init__(self):
        self.persistence_file = "data/governance_tasks.json"
        self._tasks: Dict[str, ReviewTask] = {}
        self._load_tasks()
        # Threshold for auto-approval
        self.AUTO_APPROVE_THRESHOLD = 0.95

    def _save_tasks(self):
        with open(self.persistence_file, "w") as f:
            json.dump({k: t.to_dict() for k, t in self._tasks.items()}, f, indent=2)

    def _load_tasks(self):
        if os.path.exists(self.persistence_file):
            try:
                with open(self.persistence_file, "r") as f:
                    data = json.load(f)
                    self._tasks = {k: ReviewTask.from_dict(v) for k, v in data.items()}
            except:
                self._tasks = {}

    async def create_review_task(self, doc_id: str, extraction_result: Dict, task_type: str = "general") -> str:
        """
        Analyze extraction confidence and triage.
        """
        # Calculate aggregate confidence
        # Mock logic: average confidence of entities
        entities = extraction_result.get("entities", [])
        if not entities and task_type == "general":
            conf = 1.0 # No entities, nothing to review
        elif task_type in ["rule_review", "term_review"]:
            conf = 0.5 # Always review rules/terms for now
        else:
            # Mock confidence value if missing
            conf = sum([e.get("confidence", 0.8) for e in entities]) / len(entities)

        task = ReviewTask(doc_id, extraction_result, conf, task_type)
        
        if conf >= self.AUTO_APPROVE_THRESHOLD:
            task.status = "auto_approved"
            task.final_data = extraction_result
            # Trigger sync to KG (mock)
            self._sync_to_kg(task)
        else:
             task.status = "pending"

        self._tasks[task.id] = task
        self._save_tasks()
        return task.id

    async def get_pending_reviews(self) -> List[Dict]:
        """Get queue for manual review."""
        return [
            vars(t) for t in self._tasks.values() 
            if t.status == "pending"
        ]

    async def submit_review(self, task_id: str, decision: str, corrected_data: Optional[Dict], reviewer: str):
        """
        Process human feedback.
        decision: approve, reject, correct
        """
        if task_id not in self._tasks:
            raise ValueError("Task not found")
        
        task = self._tasks[task_id]
        task.status = decision
        task.reviewer_id = reviewer
        
        if decision == "correct" and corrected_data:
            task.final_data = corrected_data
            self._save_feedback_for_training(task.extracted_data, corrected_data)
        elif decision == "approve":
            task.final_data = task.extracted_data
        
        if decision in ["approve", "correct"]:
            await self._sync_to_knowledge_store(task)
            
        self._save_tasks()
        return task.status

    async def _sync_to_knowledge_store(self, task: ReviewTask):
        """Sync approved data to the persistent Knowledge Store."""
        from app.services.knowledge_store_service import knowledge_store
        
        data = task.final_data or task.extracted_data
        
        if task.task_type == "rule_review":
            # Extract rules from the result
            rules = data.get("rules", [])
            for rule in rules:
                if rule.get("status") == "success":
                    knowledge_store.add_rule(rule)
                    print(f"[SYNC] Rule added to Knowledge Store: {rule.get('subject')}")
                    
        elif task.task_type == "term_review":
            # Extract terms/entities
            entities = data.get("entities", [])
            terms_to_add = []
            for e in entities:
                terms_to_add.append({
                    "term": e.term if hasattr(e, 'term') else e.get("term"),
                    "code": e.suggestion if hasattr(e, 'suggestion') else e.get("suggestion"),
                    "display": e.get("display") or e.get("term"),
                    "system": "SNOMED-CT",
                    "status": "APPROVED"
                })
            if terms_to_add:
                knowledge_store.add_terms(terms_to_add)
                print(f"[SYNC] {len(terms_to_add)} terms synced to Knowledge Store.")

    def _save_feedback_for_training(self, original: Dict, corrected: Dict):
        """Save pair for Future Fine-Tuning (DeepKE)."""
        # Store as JSONL or similar
        print("Saving feedback for model improvement...")

# Singleton
governance_service = GovernanceService()
