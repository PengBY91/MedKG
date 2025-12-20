from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from app.services.workflow_engine import WorkflowEngine
from app.core.auth import get_current_user

from app.services.workflow_engine import workflow_engine

router = APIRouter()

# Pydantic models
class WorkflowStart(BaseModel):
    definition_id: str
    context: dict

class TaskComplete(BaseModel):
    result: str  # approved, rejected, completed
    comments: Optional[str] = ""

@router.get("/definitions")
async def get_workflow_definitions(
    current_user: dict = Depends(get_current_user)
):
    """Get available workflow definitions."""
    definitions = [
        {
            "id": d.id,
            "name": d.name,
            "type": d.type,
            "version": d.version,
            "status": d.status
        }
        for d in workflow_engine.definitions.values()
    ]
    return {"items": definitions}

@router.post("/instances")
async def start_workflow(
    workflow_data: WorkflowStart,
    current_user: dict = Depends(get_current_user)
):
    """Start a new workflow instance."""
    try:
        instance = await workflow_engine.start_workflow(
            definition_id=workflow_data.definition_id,
            tenant_id=current_user.get("tenant_id", "default"),
            context=workflow_data.context,
            initiator=current_user["username"]
        )
        return instance
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/instances")
async def get_workflow_instances(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get workflow instances."""
    instances = await workflow_engine.get_workflow_instances(
        tenant_id=current_user.get("tenant_id", "default"),
        status=status
    )
    return {"items": instances}

@router.get("/instances/{instance_id}")
async def get_workflow_instance(
    instance_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get workflow instance detail."""
    instance = workflow_engine.instances.get(instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Workflow instance not found")
    return workflow_engine._instance_to_dict(instance)

@router.get("/tasks")
async def get_user_tasks(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get tasks assigned to current user."""
    tasks = await workflow_engine.get_user_tasks(
        user_id=current_user["username"],
        tenant_id=current_user.get("tenant_id", "default"),
        status=status
    )
    return {"items": tasks}

@router.post("/tasks/{task_id}/complete")
async def complete_task(
    task_id: str,
    task_data: TaskComplete,
    current_user: dict = Depends(get_current_user)
):
    """Complete a workflow task."""
    try:
        task = await workflow_engine.complete_task(
            task_id=task_id,
            user_id=current_user["username"],
            result=task_data.result,
            comments=task_data.comments
        )
        return task
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/tasks/{task_id}")
async def get_task(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get task detail."""
    task = workflow_engine.tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return workflow_engine._task_to_dict(task)
