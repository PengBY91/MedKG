from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import uuid
import json
import logging
import os
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.base import SessionLocal
from app.db.models import (
    WorkflowDefinition as WorkflowDefinitionModel,
    WorkflowInstance as WorkflowInstanceModel,
    WorkflowTask as WorkflowTaskModel
)

logger = logging.getLogger(__name__)

class WorkflowStatus(Enum):
    """Workflow instance status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskStatus(Enum):
    """Task status."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"

# The WorkflowDefinition, WorkflowInstance, and WorkflowTask classes are replaced by their respective database models

class WorkflowEngine:
    """Lightweight workflow execution engine."""
    
    def __init__(self):
        # Definitions cached in memory but persisted in DB
        self.definitions_cache: Dict[str, Dict] = {}
        
        # Create default workflow templates
        self._create_default_templates()
        # self._load_state()  # Replaced by DB queries on demand

    
    def _create_default_templates(self):
        """Standardize default workflow templates in database."""
        db = SessionLocal()
        try:
            templates = [
                {
                    "name": "术语审核流程",
                    "type": "terminology_review",
                    "nodes": [
                        {"id": "start", "type": "start", "name": "开始"},
                        {"id": "submit", "type": "task", "name": "提交审核", "task_type": "submit"},
                        {"id": "review", "type": "task", "name": "初审", "task_type": "approval", "assignee_role": "reviewer"},
                        {"id": "approve", "type": "task", "name": "终审", "task_type": "approval", "assignee_role": "admin"},
                        {"id": "publish", "type": "auto", "name": "发布"},
                        {"id": "end", "type": "end", "name": "结束"}
                    ],
                    "transitions": [
                        {"from": "start", "to": "submit"},
                        {"from": "submit", "to": "review"},
                        {"from": "review", "to": "approve", "condition": "approved"},
                        {"from": "review", "to": "submit", "condition": "rejected"},
                        {"from": "approve", "to": "publish", "condition": "approved"},
                        {"from": "approve", "to": "review", "condition": "rejected"},
                        {"from": "publish", "to": "end"}
                    ]
                },
                {
                    "name": "规则发布流程",
                    "type": "rule_approval",
                    "nodes": [
                        {"id": "start", "type": "start", "name": "开始"},
                        {"id": "compile", "type": "auto", "name": "编译规则"},
                        {"id": "test", "type": "task", "name": "沙箱测试", "task_type": "review"},
                        {"id": "approve", "type": "task", "name": "审批", "task_type": "approval", "assignee_role": "admin"},
                        {"id": "deploy", "type": "auto", "name": "部署"},
                        {"id": "end", "type": "end", "name": "结束"}
                    ],
                    "transitions": [
                        {"from": "start", "to": "compile"},
                        {"from": "compile", "to": "test"},
                        {"from": "test", "to": "approve", "condition": "passed"},
                        {"from": "test", "to": "compile", "condition": "failed"},
                        {"from": "approve", "to": "deploy", "condition": "approved"},
                        {"from": "approve", "to": "test", "condition": "rejected"},
                        {"from": "deploy", "to": "end"}
                    ]
                },
                {
                    "name": "全流程治理流水线",
                    "type": "governance_pipeline",
                    "nodes": [
                        {"id": "start", "type": "start", "name": "流水线启动"},
                        {"id": "ingest", "type": "auto", "name": "政策文档解析", "action": "deepke_extraction"},
                        {"id": "terminology", "type": "task", "name": "术语标准化核对", "task_type": "review", "assignee_role": "reviewer"},
                        {"id": "extraction", "type": "auto", "name": "规则语义编译", "action": "nlp_compilation"},
                        {"id": "review", "type": "task", "name": "规则风控审核", "task_type": "approval", "assignee_role": "admin"},
                        {"id": "end", "type": "end", "name": "流水线完成"}
                    ],
                    "transitions": [
                        {"from": "start", "to": "ingest"},
                        {"from": "ingest", "to": "terminology"},
                        {"from": "terminology", "to": "extraction", "condition": "approved"},
                        {"from": "extraction", "to": "review"},
                        {"from": "review", "to": "end", "condition": "approved"},
                        {"from": "review", "to": "extraction", "condition": "rejected"}
                    ]
                }
            ]
            
            for t in templates:
                # Check for existing
                existing = db.query(WorkflowDefinitionModel).filter(
                    WorkflowDefinitionModel.type == t["type"]
                ).first()
                
                if existing:
                    existing.nodes = json.dumps(t["nodes"])
                    existing.transitions = json.dumps(t["transitions"])
                    existing.name = t["name"]
                else:
                    new_def = WorkflowDefinitionModel(
                        id=str(uuid.uuid4()),
                        tenant_id="default",
                        name=t["name"],
                        type=t["type"],
                        nodes=json.dumps(t["nodes"]),
                        transitions=json.dumps(t["transitions"])
                    )
                    db.add(new_def)
            
            db.commit()
            
            # Update cache
            all_defs = db.query(WorkflowDefinitionModel).all()
            self.definitions_cache = {d.id: self._definition_to_dict(d) for d in all_defs}
        finally:
            db.close()
        
    async def _move_to_next(self, db: Session, instance: WorkflowInstanceModel, condition: str = "default"):
        """Move to next node based on condition in database."""
        definition = self.definitions_cache.get(instance.definition_id)
        if not definition:
             # Refresh cache if missing
             all_defs = db.query(WorkflowDefinitionModel).all()
             self.definitions_cache = {d.id: self._definition_to_dict(d) for d in all_defs}
             definition = self.definitions_cache.get(instance.definition_id)

        current_node = instance.current_node
        transitions = definition.get("transitions", [])
        
        transition = next(
            (t for t in transitions 
             if t["from"] == current_node and t.get("condition", "default") == condition),
            None
        )
        
        if transition:
            await self._execute_node_with_db(db, instance, transition["to"])

    
    async def start_workflow(
        self,
        definition_id: str,
        tenant_id: str,
        context: dict,
        initiator: str
    ) -> Dict[str, Any]:
        """Start a new workflow instance and save to database."""
        db = SessionLocal()
        try:
            instance_id = str(uuid.uuid4())
            instance = WorkflowInstanceModel(
                id=instance_id,
                tenant_id=tenant_id,
                definition_id=definition_id,
                status=WorkflowStatus.RUNNING.value,
                current_node="start",
                context=json.dumps(context),
                initiator=initiator,
                started_at=datetime.utcnow()
            )
            db.add(instance)
            db.commit()
            
            # Start execution from "start" node
            await self._execute_node_with_db(db, instance, "start")
            
            db.commit()
            db.refresh(instance)
            return self._instance_to_dict(instance)
        finally:
            db.close()
    
    async def _execute_node_with_db(self, db: Session, instance: WorkflowInstanceModel, node_id: str):
        """Execute a node using database for state persistence."""
        definition = self.definitions_cache.get(instance.definition_id)
        if not definition:
            return
            
        nodes = definition.get("nodes", [])
        node = next((n for n in nodes if n["id"] == node_id), None)
        if not node:
            return
            
        instance.current_node = node_id
        
        if node["type"] == "start":
            await self._move_to_next(db, instance, "default")
            
        elif node["type"] == "task":
            new_task = WorkflowTaskModel(
                id=str(uuid.uuid4()),
                tenant_id=instance.tenant_id,
                instance_id=instance.id,
                node_id=node_id,
                type=node.get("task_type", "review"),
                status=TaskStatus.PENDING.value,
                assignee=f"role:{node['assignee_role']}" if "assignee_role" in node else None
            )
            db.add(new_task)
            
        elif node["type"] == "auto":
            action = node.get("action")
            # Simulation logic
            import asyncio
            await asyncio.sleep(0.5)
            
            if action == "nlp_compilation":
                ctx = json.loads(instance.context)
                ctx["compiled_rules_count"] = 1
                instance.context = json.dumps(ctx)
                
            await self._move_to_next(db, instance, "default")
            
        elif node["type"] == "end":
            instance.status = WorkflowStatus.COMPLETED.value
            instance.completed_at = datetime.utcnow()
    
    
    async def complete_task(
        self,
        task_id: str,
        user_id: str,
        result: str,
        comments: str = ""
    ) -> Dict[str, Any]:
        """Complete a workflow task in database."""
        db = SessionLocal()
        try:
            task = db.query(WorkflowTaskModel).filter(WorkflowTaskModel.id == task_id).first()
            if not task:
                raise ValueError("Task not found")
            
            task.status = TaskStatus.COMPLETED.value
            task.result = result
            task.comments = comments
            task.completed_at = datetime.utcnow()
            
            instance = db.query(WorkflowInstanceModel).filter(
                WorkflowInstanceModel.id == task.instance_id
            ).first()
            
            if instance:
                await self._move_to_next(db, instance, result)
            
            db.commit()
            return self._task_to_dict(task)
        finally:
            db.close()
    
    async def get_user_tasks(
        self,
        user_id: str,
        tenant_id: str,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get tasks from database."""
        db = SessionLocal()
        try:
            query = db.query(WorkflowTaskModel).filter(WorkflowTaskModel.tenant_id == tenant_id)
            # Simple permission check
            if user_id != "admin":
                query = query.filter(WorkflowTaskModel.assignee.in_([user_id, "role:reviewer", "role:admin"]))
            
            if status:
                query = query.filter(WorkflowTaskModel.status == status)
                
            tasks = query.order_by(desc(WorkflowTaskModel.created_at)).all()
            return [self._task_to_dict(t) for t in tasks]
        finally:
            db.close()
    
    async def get_workflow_instances(
        self,
        tenant_id: str,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get instances from database."""
        db = SessionLocal()
        try:
            query = db.query(WorkflowInstanceModel).filter(WorkflowInstanceModel.tenant_id == tenant_id)
            if status:
                query = query.filter(WorkflowInstanceModel.status == status)
            
            instances = query.order_by(desc(WorkflowInstanceModel.created_at)).all()
            return [self._instance_to_dict(i) for i in instances]
        finally:
            db.close()
            
    def _definition_to_dict(self, d: WorkflowDefinitionModel) -> Dict:
        return {
            "id": d.id,
            "tenant_id": d.tenant_id,
            "name": d.name,
            "type": d.type,
            "nodes": json.loads(d.nodes) if d.nodes else [],
            "transitions": json.loads(d.transitions) if d.transitions else [],
            "status": d.status
        }

    def _instance_to_dict(self, i: WorkflowInstanceModel) -> Dict:
        return {
            "id": i.id,
            "tenant_id": i.tenant_id,
            "definition_id": i.definition_id,
            "status": i.status,
            "current_node": i.current_node,
            "context": json.loads(i.context) if i.context else {},
            "initiator": i.initiator,
            "created_at": i.created_at.isoformat() if i.created_at else None,
            "started_at": i.started_at.isoformat() if i.started_at else None,
            "completed_at": i.completed_at.isoformat() if i.completed_at else None
        }

    def _task_to_dict(self, t: WorkflowTaskModel) -> Dict:
        return {
            "id": t.id,
            "tenant_id": t.tenant_id,
            "instance_id": t.instance_id,
            "node_id": t.node_id,
            "type": t.type,
            "status": t.status,
            "assignee": t.assignee,
            "result": t.result,
            "comments": t.comments,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "completed_at": t.completed_at.isoformat() if t.completed_at else None
        }

    def _save_state(self):
        pass

    def _load_state(self):
        pass

# Singleton instance for high-level orchestration
workflow_engine = WorkflowEngine()
