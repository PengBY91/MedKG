import asyncio
from typing import Callable, Any
from dataclasses import dataclass
from enum import Enum
import uuid

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class Task:
    id: str
    name: str
    func: Callable
    args: tuple
    kwargs: dict
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: str = None

class AsyncTaskQueue:
    def __init__(self, max_workers: int = 3):
        self.queue = asyncio.Queue()
        self.tasks = {}
        self.max_workers = max_workers
        self.workers = []
        self.running = False
    
    async def start(self):
        """Start worker pool."""
        self.running = True
        self.workers = [
            asyncio.create_task(self._worker(i))
            for i in range(self.max_workers)
        ]
    
    async def stop(self):
        """Stop worker pool."""
        self.running = False
        await self.queue.join()
        for worker in self.workers:
            worker.cancel()
    
    async def _worker(self, worker_id: int):
        """Worker coroutine."""
        while self.running:
            try:
                task = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                
                # Update status
                task.status = TaskStatus.RUNNING
                
                try:
                    # Execute task
                    if asyncio.iscoroutinefunction(task.func):
                        result = await task.func(*task.args, **task.kwargs)
                    else:
                        result = task.func(*task.args, **task.kwargs)
                    
                    task.result = result
                    task.status = TaskStatus.COMPLETED
                    
                except Exception as e:
                    task.error = str(e)
                    task.status = TaskStatus.FAILED
                
                finally:
                    self.queue.task_done()
                    
            except asyncio.TimeoutError:
                continue
    
    def submit(self, name: str, func: Callable, *args, **kwargs) -> str:
        """Submit a task to the queue."""
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            name=name,
            func=func,
            args=args,
            kwargs=kwargs
        )
        
        self.tasks[task_id] = task
        asyncio.create_task(self.queue.put(task))
        
        return task_id
    
    def get_status(self, task_id: str) -> dict:
        """Get task status."""
        task = self.tasks.get(task_id)
        if not task:
            return {"error": "Task not found"}
        
        return {
            "id": task.id,
            "name": task.name,
            "status": task.status.value,
            "result": task.result,
            "error": task.error
        }

# Global task queue instance
task_queue = AsyncTaskQueue()
