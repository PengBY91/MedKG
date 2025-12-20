import logging
import time
import json
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("medical_governance")

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        # Log request
        start_time = time.time()
        
        # Extract request info
        request_info = {
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "auth_header": request.headers.get("authorization")[:30] + "..." if request.headers.get("authorization") else None,
        }

        
        logger.info(f"Request started: {json.dumps(request_info)}")
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            response_info = {
                **request_info,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2)
            }
            
            logger.info(f"Request completed: {json.dumps(response_info)}")
            
            # Add custom headers
            response.headers["X-Process-Time"] = str(duration)
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Request failed: {json.dumps({**request_info, 'error': str(e), 'duration_ms': round(duration * 1000, 2)})}")
            raise

def log_operation(operation: str, user: str, details: dict):
    """
    Log important business operations for audit trail.
    """
    audit_log = {
        "timestamp": time.time(),
        "operation": operation,
        "user": user,
        "details": details
    }
    logger.info(f"AUDIT: {json.dumps(audit_log)}")
