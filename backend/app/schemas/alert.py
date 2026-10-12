from typing import Optional
from pydantic import BaseModel

class AlertResponse(BaseModel):
    id: str
    shipment_id: str
    sensor_id: Optional[str] = None
    excursion_event_id: Optional[str] = None
    type: str
    severity: str
    status: str
    title: str
    message: str
    created_at: str
    updated_at: str
    acknowledged_at: Optional[str] = None

class AlertAcknowledgeRequest(BaseModel):
    acknowledged_by: Optional[str] = "operator"
