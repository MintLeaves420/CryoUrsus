from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class AssessmentCreateRequest(BaseModel):
    review_status: str
    reviewer_label: Optional[str] = "Demo Operator"
    review_note: Optional[str] = None

class AssessmentResponse(BaseModel):
    id: Optional[str] = None
    shipment_id: str
    review_status: str
    review_note: Optional[str] = None
    reviewer_label: Optional[str] = None
    created_at: Optional[str] = None
    method_version: str = "demo-v1"
    demo_score: Optional[float] = None
    demo_label: Optional[str] = None
    features: Optional[Dict[str, Any]] = None
    explanation: Optional[List[str]] = None
    disclaimer: str = "Simulation estimate only — not validated for product release or clinical use."
