from typing import Optional, List
from pydantic import BaseModel

class ReadingResponse(BaseModel):
    id: int
    shipment_id: str
    sensor_id: str
    timestamp: str
    temperature_c: Optional[float] = None
    quality_status: str
    source: str = "simulated"
    scenario: Optional[str] = None
    created_at: str

class ReadingsListResponse(BaseModel):
    shipment_id: str
    total: int
    readings: List[ReadingResponse]
