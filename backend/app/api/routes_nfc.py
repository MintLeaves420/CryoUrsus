from fastapi import APIRouter, HTTPException
from backend.app.schemas.nfc import NFCTransferResponse
from backend.app.services.nfc_service import get_nfc_transfer_by_id

router = APIRouter(prefix="/nfc-transfers", tags=["NFC"])

@router.get("/{transfer_id}", response_model=NFCTransferResponse)
def get_nfc_transfer(transfer_id: str):
    res = get_nfc_transfer_by_id(transfer_id)
    if not res:
        raise HTTPException(status_code=404, detail={
            "error": {"code": "not_found", "message": f"NFC transfer record '{transfer_id}' not found."}
        })
    return res
