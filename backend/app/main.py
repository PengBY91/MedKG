from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from dotenv import load_dotenv
from app.core.config import settings
from app.core.exceptions import (
    GovernanceException,
    governance_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from app.core.logging import LoggingMiddleware, setup_logging
from app.core.task_queue import task_queue
import asyncio

# Load environment variables from .env file
load_dotenv()

# Initialize logging
setup_logging()


# Force reload timestamp: 2025-12-27 - 2
app = FastAPI(
    title=settings.PROJECT_NAME,

    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="Medical Knowledge Graph Terminology and Rule Governance Tool",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging middleware
app.add_middleware(LoggingMiddleware)

# Exception handlers
app.add_exception_handler(GovernanceException, governance_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

@app.on_event("startup")
async def startup_event():
    """Start background tasks and initialize DB on startup."""
    from app.db.base import init_db
    from app.core.kg import neo4j_service
    
    init_db()
    asyncio.create_task(task_queue.start())
    await neo4j_service.initialize()

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    from app.core.kg import neo4j_service
    await task_queue.stop()
    await neo4j_service.close()

@app.get("/")
async def root():
    return {"message": "Welcome to Medical Governance Tool API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

from app.api.api_v1.api import api_router

app.include_router(api_router, prefix=settings.API_V1_STR)



