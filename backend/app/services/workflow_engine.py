from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import uuid
import json
import logging
import os

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

class WorkflowDefinition:
    """Workflow definition model."""
    def __init__(self, name: str, tenant_id: str, workflow_type: str):
        self.id = str(uuid.uuid4())
        self.tenant_id = tenant_id
        self.name = name
        self.type = workflow_type
        self.version = 1
        self.nodes = []  # List of workflow nodes
        self.transitions = []  # List of transitions between nodes
        self.status = "active"
        self.created_at = datetime.utcnow().isoformat()

class WorkflowInstance:
    """Workflow instance (execution)."""
    def __init__(self, definition_id: str, tenant_id: str, context: dict):
        self.id = str(uuid.uuid4())
        self.tenant_id = tenant_id
        self.definition_id = definition_id
        self.status = WorkflowStatus.PENDING.value
        self.current_node = "start"
        self.context = context  # Workflow variables
        self.tasks = []  # List of task IDs
        self.created_at = datetime.utcnow().isoformat()
        self.started_at = None
        self.completed_at = None

class WorkflowTask:
    """Workflow task (user action)."""
    def __init__(
        self,
        instance_id: str,
        tenant_id: str,
        node_id: str,
        task_type: str,
        assignee: Optional[str] = None
    ):
        self.id = str(uuid.uuid4())
        self.tenant_id = tenant_id
        self.instance_id = instance_id
        self.node_id = node_id
        self.type = task_type  # approval, review, input
        self.status = TaskStatus.PENDING.value
        self.assignee = assignee
        self.data = {}
        self.result = None
        self.comments = ""
        self.created_at = datetime.utcnow().isoformat()
        self.completed_at = None

class WorkflowEngine:
    """Lightweight workflow execution engine."""
    
    def __init__(self):
        self.definitions: Dict[str, WorkflowDefinition] = {}
        self.instances: Dict[str, WorkflowInstance] = {}
        self.tasks: Dict[str, WorkflowTask] = {}
        
        self.state_file = "workflow_state.json"
        
        # Create default workflow templates
        self._create_default_templates()
        self._load_state()
        
        # Ensure default templates are always present (may override loaded ones if ID matches)
        self._create_default_templates()

    
    def _create_default_templates(self):
        """Create default workflow templates."""
        # Terminology Review Workflow
        term_workflow = WorkflowDefinition(
            name="术语审核流程",
            tenant_id="default",
            workflow_type="terminology_review"
        )
        term_workflow.nodes = [
            {"id": "start", "type": "start", "name": "开始"},
            {"id": "submit", "type": "task", "name": "提交审核", "task_type": "submit"},
            {"id": "review", "type": "task", "name": "初审", "task_type": "approval", "assignee_role": "reviewer"},
            {"id": "approve", "type": "task", "name": "终审", "task_type": "approval", "assignee_role": "admin"},
            {"id": "publish", "type": "auto", "name": "发布"},
            {"id": "end", "type": "end", "name": "结束"}
        ]
        term_workflow.transitions = [
            {"from": "start", "to": "submit"},
            {"from": "submit", "to": "review"},
            {"from": "review", "to": "approve", "condition": "approved"},
            {"from": "review", "to": "submit", "condition": "rejected"},
            {"from": "approve", "to": "publish", "condition": "approved"},
            {"from": "approve", "to": "review", "condition": "rejected"},
            {"from": "publish", "to": "end"}
        ]
        self.definitions[term_workflow.id] = term_workflow
        
        # Rule Approval Workflow
        rule_workflow = WorkflowDefinition(
            name="规则发布流程",
            tenant_id="default",
            workflow_type="rule_approval"
        )
        rule_workflow.nodes = [
            {"id": "start", "type": "start", "name": "开始"},
            {"id": "compile", "type": "auto", "name": "编译规则"},
            {"id": "test", "type": "task", "name": "沙箱测试", "task_type": "review"},
            {"id": "approve", "type": "task", "name": "审批", "task_type": "approval", "assignee_role": "admin"},
            {"id": "deploy", "type": "auto", "name": "部署"},
            {"id": "end", "type": "end", "name": "结束"}
        ]
        rule_workflow.transitions = [
            {"from": "start", "to": "compile"},
            {"from": "compile", "to": "test"},
            {"from": "test", "to": "approve", "condition": "passed"},
            {"from": "test", "to": "compile", "condition": "failed"},
            {"from": "approve", "to": "deploy", "condition": "approved"},
            {"from": "approve", "to": "test", "condition": "rejected"},
            {"from": "deploy", "to": "end"}
        ]
        self.definitions[rule_workflow.id] = rule_workflow

        # 3. Governance Pipeline (End-to-End)
        gov_pipeline = WorkflowDefinition(
            name="全流程治理流水线",
            tenant_id="default",
            workflow_type="governance_pipeline"
        )
        gov_pipeline.nodes = [
            {"id": "start", "type": "start", "name": "流水线启动"},
            {"id": "ingest", "type": "auto", "name": "政策文档解析", "action": "deepke_extraction"},
            {"id": "terminology", "type": "task", "name": "术语标准化核对", "task_type": "review", "assignee_role": "reviewer"},
            {"id": "extraction", "type": "auto", "name": "规则语义编译", "action": "nlp_compilation"},
            {"id": "review", "type": "task", "name": "规则风控审核", "task_type": "approval", "assignee_role": "admin"},
            {"id": "end", "type": "end", "name": "流水线完成"}
        ]
        gov_pipeline.transitions = [
            {"from": "start", "to": "ingest"},
            {"from": "ingest", "to": "terminology"},
            {"from": "terminology", "to": "extraction", "condition": "approved"},
            {"from": "extraction", "to": "review"},
            {"from": "review", "to": "end", "condition": "approved"},
            {"from": "review", "to": "extraction", "condition": "rejected"}
        ]
        self.definitions[gov_pipeline.id] = gov_pipeline
        
    def _create_sample_instances(self):
        """Create sample workflow instances and tasks for demonstration."""
        # 1. Terminology Review Task
        term_def = next(d for d in self.definitions.values() if d.type == "terminology_review")
        inst1 = WorkflowInstance(term_def.id, "default", {"term": "二型糖伴酮症", "initiator": "reviewer"})
        inst1.status = WorkflowStatus.RUNNING.value
        inst1.started_at = "2024-12-18T09:00:00Z"
        self.instances[inst1.id] = inst1
        
        task1 = WorkflowTask(inst1.id, "default", "review", "approval", assignee="role:reviewer")
        task1.status = TaskStatus.IN_PROGRESS.value
        task1.data = {"content": "诊断术语标准化：'二型糖伴酮症' -> 'E11.101 (2型糖尿病伴有酮症酸中毒)'"}
        self.tasks[task1.id] = task1
        inst1.tasks.append(task1.id)
        inst1.current_node = "review"
        
        # 2. Rule Approval Task
        rule_def = next(d for d in self.definitions.values() if d.type == "rule_approval")
        inst2 = WorkflowInstance(rule_def.id, "default", {"policy": "门诊大病政策2024", "initiator": "admin"})
        inst2.status = WorkflowStatus.RUNNING.value
        inst2.started_at = "2024-12-19T10:30:00Z"
        self.instances[inst2.id] = inst2
        
        task2 = WorkflowTask(inst2.id, "default", "approve", "approval", assignee="role:admin")
        task2.status = TaskStatus.PENDING.value
        task2.data = {"content": "规则审核：自费药比例控制规则 (ID: RULE-001)"}
        self.tasks[task2.id] = task2
        inst2.tasks.append(task2.id)
        inst2.current_node = "approve"

        # 3. Completed Task for History
        inst3 = WorkflowInstance(term_def.id, "default", {"term": "高血压1级", "initiator": "admin"})
        inst3.status = WorkflowStatus.COMPLETED.value
        inst3.started_at = "2024-12-17T08:00:00Z"
        inst3.completed_at = "2024-12-17T14:30:00Z"
        self.instances[inst3.id] = inst3
        
        task3 = WorkflowTask(inst3.id, "default", "review", "approval", assignee="role:reviewer")
        task3.status = TaskStatus.COMPLETED.value
        task3.result = "approved"
        task3.comments = "符合ICD-10标准"
        task3.completed_at = "2024-12-17T11:00:00Z"
        self.tasks[task3.id] = task3
        inst3.tasks.append(task3.id)

    
    async def start_workflow(
        self,
        definition_id: str,
        tenant_id: str,
        context: dict,
        initiator: str
    ) -> Dict[str, Any]:
        """Start a new workflow instance."""
        definition = self.definitions.get(definition_id)
        if not definition:
            raise ValueError("Workflow definition not found")
        
        # Create instance
        instance = WorkflowInstance(definition_id, tenant_id, context)
        instance.status = WorkflowStatus.RUNNING.value
        instance.started_at = datetime.utcnow().isoformat()
        instance.context["initiator"] = initiator
        
        self.instances[instance.id] = instance
        self._save_state()
        
        # Move to first node
        await self._execute_node(instance, "start")
        
        return self._instance_to_dict(instance)
    
    async def _execute_node(self, instance: WorkflowInstance, node_id: str):
        """Execute a workflow node."""
        definition = self.definitions[instance.definition_id]
        node = next((n for n in definition.nodes if n["id"] == node_id), None)
        
        if not node:
            return
        
        instance.current_node = node_id
        
        if node["type"] == "start":
            # Start nodes automatically transition to next node
            logger.info(f"Starting workflow instance {instance.id} at start node")
            await self._move_to_next(instance, "default")
        
        elif node["type"] == "task":
            # Create task
            task = WorkflowTask(
                instance_id=instance.id,
                tenant_id=instance.tenant_id,
                node_id=node_id,
                task_type=node.get("task_type", "review")
            )
            
            # Assign task
            if "assignee_role" in node:
                task.assignee = f"role:{node['assignee_role']}"
            
            self.tasks[task.id] = task
            instance.tasks.append(task.id)
            
        elif node["type"] == "auto":
            # Auto execute based on action
            action = node.get("action")
            logger.info(f"Executing auto node: {node_id} (Action: {action}) for instance {instance.id}")
            
            # In a real system, we'd look up the action handler
            # For now, we simulate success for known actions
            if action == "deepke_extraction":
                # Simulated extraction delay
                import asyncio
                await asyncio.sleep(1)
                logger.info(f"Auto-extraction completed for {instance.id}")
            elif action == "nlp_compilation":
                # Simulate rule generation using text from context
                import asyncio
                await asyncio.sleep(1)
                text = instance.context.get("document_content", "")
                entities = instance.context.get("entities", [])
                logger.info(f"NLP compilation simulated for {instance.id} (Content length: {len(text)})")
                # We could attach results to context here if needed
                instance.context["compiled_rules_count"] = len(entities) // 2 + 1 if entities else 1
            
            # Auto nodes typically transition with the "default" condition unless specified
            await self._move_to_next(instance, "default")
        
        elif node["type"] == "end":
            # Complete workflow
            instance.status = WorkflowStatus.COMPLETED.value
            instance.completed_at = datetime.utcnow().isoformat()
        
        self._save_state()
    
    async def _move_to_next(self, instance: WorkflowInstance, condition: str = "default"):
        """Move to next node based on condition."""
        definition = self.definitions[instance.definition_id]
        current_node = instance.current_node
        
        # Find matching transition
        transition = next(
            (t for t in definition.transitions 
             if t["from"] == current_node and t.get("condition", "default") == condition),
            None
        )
        
        if transition:
            await self._execute_node(instance, transition["to"])
    
    async def complete_task(
        self,
        task_id: str,
        user_id: str,
        result: str,
        comments: str = ""
    ) -> Dict[str, Any]:
        """Complete a workflow task."""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError("Task not found")
        
        # Update task
        task.status = TaskStatus.COMPLETED.value
        task.result = result
        task.comments = comments
        task.completed_at = datetime.utcnow().isoformat()
        
        # Get instance
        instance = self.instances.get(task.instance_id)
        if not instance:
            raise ValueError("Workflow instance not found")
        
        # Move to next node
        await self._move_to_next(instance, result)
        self._save_state()
        
        return self._task_to_dict(task)
    
    async def get_user_tasks(
        self,
        user_id: str,
        tenant_id: str,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get tasks assigned to user."""
        tasks = [
            t for t in self.tasks.values()
            if t.tenant_id == tenant_id and (
                t.assignee == user_id or
                t.assignee == f"role:admin"  # Simplified role matching
            )
        ]
        
        if status:
            tasks = [t for t in tasks if t.status == status]
        
        return [self._task_to_dict(t) for t in tasks]
    
    async def get_workflow_instances(
        self,
        tenant_id: str,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get workflow instances."""
        instances = [i for i in self.instances.values() if i.tenant_id == tenant_id]
        
        if status:
            instances = [i for i in instances if i.status == status]
        
        return [self._instance_to_dict(i) for i in instances]
    
    def _instance_to_dict(self, instance: WorkflowInstance) -> Dict[str, Any]:
        """Convert instance to dict."""
        return {
            "id": instance.id,
            "tenant_id": instance.tenant_id,
            "definition_id": instance.definition_id,
            "status": instance.status,
            "current_node": instance.current_node,
            "context": instance.context,
            "tasks": instance.tasks,
            "created_at": instance.created_at,
            "started_at": instance.started_at,
            "completed_at": instance.completed_at
        }
    
    def _task_to_dict(self, task: WorkflowTask) -> Dict[str, Any]:
        """Convert task to dict."""
        return {
            "id": task.id,
            "tenant_id": task.tenant_id,
            "instance_id": task.instance_id,
            "node_id": task.node_id,
            "type": task.type,
            "status": task.status,
            "assignee": task.assignee,
            "data": task.data,
            "result": task.result,
            "comments": task.comments,
            "created_at": task.created_at,
            "completed_at": task.completed_at
        }

    def _save_state(self):
        """Save engine state to file."""
        try:
            state = {
                "instances": {k: self._instance_to_dict(v) for k, v in self.instances.items()},
                "tasks": {k: self._task_to_dict(v) for k, v in self.tasks.items()}
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save workflow state: {str(e)}")

    def _load_state(self):
        """Load engine state from file."""
        if not os.path.exists(self.state_file):
            return
        
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
            
            for k, v in state.get("instances", {}).items():
                inst = WorkflowInstance(v["definition_id"], v["tenant_id"], v["context"])
                inst.id = k
                inst.status = v["status"]
                inst.current_node = v["current_node"]
                inst.tasks = v["tasks"]
                inst.created_at = v["created_at"]
                inst.started_at = v.get("started_at")
                inst.completed_at = v.get("completed_at")
                self.instances[k] = inst
            
            for k, v in state.get("tasks", {}).items():
                task = WorkflowTask(v["instance_id"], v["tenant_id"], v["node_id"], v["type"], v.get("assignee"))
                task.id = k
                task.status = v["status"]
                task.data = v.get("data", {})
                task.result = v.get("result")
                task.comments = v.get("comments", "")
                task.created_at = v["created_at"]
                task.completed_at = v.get("completed_at")
                self.tasks[k] = task
        except Exception as e:
            logger.error(f"Failed to load workflow state: {str(e)}")

# Singleton instance for high-level orchestration
workflow_engine = WorkflowEngine()
