from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from backend.app.schemas.reading import ReadingResponse, ReadingsListResponse
from backend.app.models.database import get_connection

router = APIRouter(prefix="/shipments/{shipment_id}/readings", tags=["Readings"])

@router.get("", response_model=ReadingsListResponse)
def get_shipment_readings(
    shipment_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
    since: Optional[str] = None,
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
):
    with get_connection() as conn:
        shipment = conn.execute("SELECT id FROM shipments WHERE id = ?", (shipment_id,)).fetchone()
        if not shipment:
            raise HTTPException(status_code=404, detail={
                "error": {"code": "not_found", "message": f"Shipment '{shipment_id}' not found."}
            })

        query = "SELECT * FROM readings WHERE shipment_id = ?"
        params = [shipment_id]

        if since:
            query += " AND timestamp > ?"
            params.append(since)

        total_row = conn.execute(
            "SELECT COUNT(*) as cnt FROM readings WHERE shipment_id = ?", (shipment_id,)
        ).fetchone()
        total = total_row["cnt"] if total_row else 0

        query += f" ORDER BY timestamp {order.upper()} LIMIT ?"
        params.append(limit)

        rows = conn.execute(query, params).fetchall()
        readings = [ReadingResponse(**dict(r)) for r in rows]

    return ReadingsListResponse(shipment_id=shipment_id, total=total, readings=readings)
