import logging
import time
import json
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable

class JsonFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs in JSON format.
    """
    def format(self, record):
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "lineno": record.lineno
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record, ensure_ascii=False)

def setup_logging(log_level=logging.INFO):
    """
    Setup structured logging with rotating file handlers.
    """
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    ))
    root_logger.addHandler(console_handler)

    # JSON File Handler (Rotating)
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "app.log"),
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(JsonFormatter())
    root_logger.addHandler(file_handler)

    # Error Log Handler
    error_handler = RotatingFileHandler(
        os.path.join(log_dir, "error.log"),
        maxBytes=10*1024*1024,
        backupCount=10,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JsonFormatter())
    root_logger.addHandler(error_handler)

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log every HTTP request and response in JSON format.
    """
    async def dispatch(self, request: Request, call_next: Callable):
        start_time = time.time()
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            log_data = {
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
                "client_ip": request.client.host if request.client else "unknown"
            }
            
            if response.status_code >= 500:
                logging.error(f"Request failed: {json.dumps(log_data)}")
            elif response.status_code >= 400:
                logging.warning(f"Request warning: {json.dumps(log_data)}")
            else:
                logging.info(f"Request completed: {json.dumps(log_data)}")
                
            return response
        except Exception as e:
            duration = time.time() - start_time
            logging.error(json.dumps({
                "method": request.method,
                "path": request.url.path,
                "error": str(e),
                "duration_ms": round(duration * 1000, 2)
            }))
            raise

def log_operation(operation: str, user: str, details: dict):
    """Log important business operations for audit trail."""
    audit_log = {
        "timestamp": datetime.utcnow().isoformat(),
        "operation": operation,
        "user": user,
        "details": details
    }
    logging.info(f"AUDIT: {json.dumps(audit_log, ensure_ascii=False)}")
