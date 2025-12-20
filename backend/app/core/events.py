import asyncio
from typing import Dict, Any, Callable, List
from dataclasses import dataclass
from enum import Enum

class EventType(Enum):
    DOCUMENT_UPLOADED = "document_uploaded"
    RULE_DRAFTED = "rule_drafted"
    TERMINOLOGY_MAPPED = "terminology_mapped"

@dataclass
class Event:
    type: EventType
    data: Dict[str, Any]

class EventBus:
    def __init__(self):
        self._handlers: Dict[EventType, List[Callable]] = {}
        self._queue = asyncio.Queue()
    
    def subscribe(self, event_type: EventType, handler: Callable):
        """Subscribe a handler to an event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    async def publish(self, event: Event):
        """Publish an event to the bus."""
        await self._queue.put(event)
    
    async def start(self):
        """Start processing events (run in background)."""
        while True:
            event = await self._queue.get()
            handlers = self._handlers.get(event.type, [])
            
            for handler in handlers:
                try:
                    await handler(event.data)
                except Exception as e:
                    print(f"Error in event handler: {e}")
            
            self._queue.task_done()

# Global event bus instance
event_bus = EventBus()

# Example handlers
async def on_document_uploaded(data: Dict[str, Any]):
    """Handler for document upload events."""
    print(f"Document uploaded: {data.get('filename')}")
    # TODO: Trigger OCR, Embedding, etc.

async def on_rule_drafted(data: Dict[str, Any]):
    """Handler for rule draft events."""
    print(f"Rule drafted: {data.get('rule_id')}")
    # TODO: Trigger syntax validation, conflict detection

# Register handlers
event_bus.subscribe(EventType.DOCUMENT_UPLOADED, on_document_uploaded)
event_bus.subscribe(EventType.RULE_DRAFTED, on_rule_drafted)
