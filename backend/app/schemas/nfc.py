from typing import Optional
from pydantic import BaseModel

class NFCTransferResponse(BaseModel):
    id: str
    shipment_id: str
    status: str
    records_transferred: int
    started_at: str
    completed_at: Optional[str] = None
    message: Optional[str] = None
    simulation_label: str = "Simulated NFC Handoff — No hardware required"
