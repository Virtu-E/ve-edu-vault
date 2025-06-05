from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, field_serializer


class WebhookRequest(BaseModel):
    event_type: str
    event_id: str
    timestamp: Optional[datetime] = None
    data: Dict[str, Any]

    @field_serializer("timestamp")
    def serialize_dt(self, timestamp: Optional[datetime], _info):
        return timestamp.isoformat() if timestamp else None
