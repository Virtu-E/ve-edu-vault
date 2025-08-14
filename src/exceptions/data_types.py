from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Single error detail structure"""

    code: str
    message: str
    field: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Standardized error response structure"""

    success: bool = False
    errors: Optional[List[ErrorDetail]] = None
    request_id: Optional[str] = None
    timestamp: Optional[str] = None
