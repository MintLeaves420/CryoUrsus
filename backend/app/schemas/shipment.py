from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from backend.app.schemas.profile import ProductProfileResponse

class SensorResponse(BaseModel):
    id: str
    shipment_id: str
    label: str
    position_x: float
    position_y: float
    position_z: float
    health_status: str
    last_valid_temperature_c: Optional[float] = None
    last_reading_at: Optional[str] = None
    created_at: str

class ShipmentCreateRequest(BaseModel):
    profile_id: str
    vial_count: int = Field(default=9, ge=1, le=9)
    sensor_count: int = Field(default=4, ge=1, le=10)
    scenario: str = Field(default="normal")
    destination_label: Optional[str] = "Demo Destination (Sample Lab B)"

class ShipmentScenarioUpdateRequest(BaseModel):
    scenario: str
    parameters: Optional[Dict[str, Any]] = None

class ShipmentResponse(BaseModel):
    id: str
    profile_id: str
    status: str
    vial_count: int
    sensor_count: int
    destination_label: Optional[str] = None
    scenario: str
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    created_at: str
    updated_at: str
    operator_review_status: Optional[str] = None
    operator_review_note: Optional[str] = None
    profile: Optional[ProductProfileResponse] = None
    sensors: List[SensorResponse] = []
    active_alerts_count: int = 0
    demo_disclaimer: str = "CryoUrsus Telemetry & Thermal Viability Model."
