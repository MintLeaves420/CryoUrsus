import uuid
from datetime import datetime, timezone
from typing import Optional
from backend.app.models.database import get_connection
from backend.app.schemas.nfc import NFCTransferResponse
from backend.app.services.audit_service import record_audit_event

def trigger_simulated_nfc_transfer(shipment_id: str) -> NFCTransferResponse:
    transfer_id = f"nfc_{uuid.uuid4().hex[:8]}"
    now_iso = datetime.now(timezone.utc).isoformat()

    with get_connection() as conn:
        # Check shipment exists and count total records
        shipment = conn.execute("SELECT id FROM shipments WHERE id = ?", (shipment_id,)).fetchone()
        if not shipment:
            raise ValueError(f"Shipment '{shipment_id}' not found.")

        readings_count = conn.execute(
            "SELECT COUNT(*) as cnt FROM readings WHERE shipment_id = ?",
            (shipment_id,),
        ).fetchone()["cnt"]

        conn.execute(
            """
            INSERT INTO nfc_transfers (
                id, shipment_id, status, records_transferred,
                started_at, completed_at, message
            ) VALUES (?, ?, 'success', ?, ?, ?, ?)
            """,
            (
                transfer_id,
                shipment_id,
                readings_count,
                now_iso,
                now_iso,
                f"Simulated local NFC data exchange complete: {readings_count} cryptographic sensor logs extracted.",
            ),
        )

    record_audit_event(
        event_type="nfc.transfer_completed",
        shipment_id=shipment_id,
        details={
            "transfer_id": transfer_id,
            "records_transferred": readings_count,
            "simulated": True,
        },
    )

    return get_nfc_transfer_by_id(transfer_id)

def get_nfc_transfer_by_id(transfer_id: str) -> Optional[NFCTransferResponse]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM nfc_transfers WHERE id = ?", (transfer_id,)
        ).fetchone()
        if not row:
            return None
        return NFCTransferResponse(**dict(row))
