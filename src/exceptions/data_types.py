from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ErrorDetail:
    """Single error detail structure"""

    code: str
    message: str
    field: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


@dataclass
class ErrorResponse:
    """Standardized error response structure"""

    success: bool = False
    errors: Optional[List[ErrorDetail]] = None
    request_id: Optional[str] = None
    timestamp: Optional[str] = None
