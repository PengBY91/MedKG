"""
API endpoints for examination standardization.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import Optional
import io
import logging

from app.services.examination_standardization_service import examination_service
from app.services.examination_kg_importer import examination_kg_importer
from app.services.examination_kg_service import examination_kg_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload")
async def upload_examination_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user: str = Query(default="system")
):
    """
    Upload a file for examination standardization.
    
    Expected file format: CSV or Excel
    Required columns: 检查项目名, 检查标准模态 (or exam_name, modality)
    
    Returns:
        Task ID for tracking progress
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith(('.csv', '.xlsx', '.xls')):
            raise HTTPException(
                status_code=400,
                detail="Unsupported file format. Please upload CSV or Excel file."
            )
        
        # Read content
        content = await file.read()
        
        # Create task
        task_id = examination_service.create_task(file.filename, user)
        
        # Process in background
        background_tasks.add_task(examination_service.process_file, task_id, content, file.filename)
        
        return {
            "success": True,
            "task_id": task_id,
            "message": "File uploaded and processing started"
        }
        
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_history(limit: int = 50):
    """
    Get historical standardization tasks.
    
    Returns:
        List of past tasks
    """
    tasks = examination_service.get_all_tasks(limit)
    return {
        "success": True,
        "tasks": tasks
    }


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """
    Get the status of a standardization task.
    
    Returns:
        Task status including progress and statistics
    """
    task = examination_service.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "success": True,
        "task": task
    }


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """
    Delete a standardization task.
    """
    success = examination_service.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found or failed to delete")
    return {
        "success": True,
        "message": "Task deleted successfully"
    }



@router.get("/tasks/{task_id}/results")
async def get_task_results(task_id: str):
    """
    Get detailed results for a completed task.
    
    Returns:
        List of standardization results
    """
    results = examination_service.get_task_results(task_id)
    
    if results is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "success": True,
        "results": results
    }


@router.put("/tasks/{task_id}/results")
async def update_task_results(
    task_id: str,
    results: list[dict]
):
    """
    Update standardization results for a task (Manual Correction).
    
    Args:
        task_id: Task ID
        results: List of corrected results
        
    Returns:
        Success status
    """
    success = examination_service.update_task_results(task_id, results)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update results. Task not found or invalid data.")
    
    return {
        "success": True,
        "message": "Results updated successfully"
    }


@router.get("/config/llm")
async def get_llm_config():
    """Get current LLM configuration."""
    return {
        "success": True,
        "config": examination_service.get_llm_config()
    }

@router.post("/config/llm")
async def update_llm_config(
    config: dict
):
    """
    Update LLM configuration.
    Expects: { "api_key": "...", "base_url": "...", "model": "..." }
    """
    api_key = config.get("api_key")
    base_url = config.get("base_url")
    model = config.get("model")
    
    if not all([api_key, base_url, model]):
        raise HTTPException(status_code=400, detail="Missing required fields")
        
    # Runtime update
    success = examination_service.reconfigure_llm(api_key, base_url, model)
    
    # Persistence update (Write to .env)
    try:
        env_path = ".env"
        # Read existing
        lines = []
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                lines = f.readlines()
        
        # Prepare new lines map
        new_env = {
            "OPENAI_API_KEY": api_key,
            "OPENAI_BASE_URL": base_url,
            "OPENAI_MODEL": model
        }
        
        final_lines = []
        processed_keys = set()
        
        for line in lines:
            key = line.split("=")[0].strip()
            if key in new_env:
                final_lines.append(f"{key}={new_env[key]}\n")
                processed_keys.add(key)
            else:
                final_lines.append(line)
        
        # Append missing
        for key, val in new_env.items():
            if key not in processed_keys:
                if final_lines and not final_lines[-1].endswith("\n"):
                    final_lines.append("\n")
                final_lines.append(f"{key}={val}\n")
                
        with open(env_path, "w") as f:
            f.writelines(final_lines)
            
    except Exception as e:
        logger.error(f"Failed to write .env: {e}")
        # Non-blocking failure
    
    if not success:
         raise HTTPException(status_code=500, detail="Failed to initialize LLM client with provided credentials")
         
    return {
        "success": True,
        "message": "Configuration updated successfully"
    }

@router.get("/tasks/{task_id}/export")
async def export_task_results(
    task_id: str,
    format: str = Query(default="csv", regex="^(csv|excel)$")
):
    """
    Export task results to CSV or Excel.
    
    Args:
        task_id: Task ID
        format: Export format ('csv' or 'excel')
        
    Returns:
        File download
    """
    content = examination_service.export_results(task_id, format)
    
    if content is None:
        raise HTTPException(status_code=404, detail="Task not found or no results available")
    
    # Prepare response
    if format == "csv":
        media_type = "text/csv"
        filename = f"examination_results_{task_id}.csv"
    else:
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"examination_results_{task_id}.xlsx"
    
    return StreamingResponse(
        io.BytesIO(content),
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )



