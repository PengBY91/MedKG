from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import traceback

class GovernanceException(Exception):
    """Base exception for governance tool."""
    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)

class TerminologyMappingError(GovernanceException):
    def __init__(self, message: str):
        super().__init__(message, code="TERMINOLOGY_ERROR")

class RuleCompilationError(GovernanceException):
    def __init__(self, message: str):
        super().__init__(message, code="RULE_COMPILATION_ERROR")

class GraphQueryError(GovernanceException):
    def __init__(self, message: str):
        super().__init__(message, code="GRAPH_QUERY_ERROR")

async def governance_exception_handler(request: Request, exc: GovernanceException):
    """Handle custom governance exceptions."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "path": str(request.url)
            }
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request parameters",
                "details": exc.errors()
            }
        }
    )

async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler."""
    print(f"Unhandled exception: {exc}")
    print(traceback.format_exc())
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred"
            }
        }
    )
