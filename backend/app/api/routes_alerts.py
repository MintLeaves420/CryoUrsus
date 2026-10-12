from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from backend.app.schemas.alert import AlertResponse, AlertAcknowledgeRequest
from backend.app.services.alert_service import list_alerts, acknowledge_alert

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("", response_model=List[AlertResponse])
def get_alerts(
    shipment_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
):
    return list_alerts(shipment_id=shipment_id, status=status)

@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
def acknowledge(alert_id: str, req: AlertAcknowledgeRequest = AlertAcknowledgeRequest()):
    updated = acknowledge_alert(alert_id, acknowledged_by=req.acknowledged_by or "operator")
    if not updated:
        raise HTTPException(status_code=404, detail={
            "error": {"code": "not_found", "message": f"Alert '{alert_id}' not found."}
        })
    return updated
