from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class ShipmentSummaryResponse(BaseModel):
    shipment_id: str
    status: str
    total_readings: int
    valid_readings_count: int
    valid_data_coverage: float
    peak_temperature_c: Optional[float] = None
    minimum_temperature_c: Optional[float] = None
    excursion_duration_seconds: float = 0.0
    crossing_count: int = 0
    max_rate_c_per_minute: float = 0.0
    data_quality_status: str
    sensors_summary: List[Dict[str, Any]] = []
    demo_score: Optional[float] = None
    demo_label: Optional[str] = None
    explanation: List[str] = []
    method_version: str = "demo-v1"
    disclaimer: str = "Simulation estimate only — not validated for product release or clinical use."
