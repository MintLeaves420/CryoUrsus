import json
import sqlite3
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from backend.app.models.database import get_connection

def record_audit_event(
    event_type: str,
    shipment_id: Optional[str] = None,
    actor_label: str = "demo-user",
    details: Optional[Dict[str, Any]] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> None:
    now_iso = datetime.now(timezone.utc).isoformat()
    details_str = json.dumps(details) if details else None

    def _insert(c: sqlite3.Connection):
        c.execute(
            """
            INSERT INTO audit_events (shipment_id, event_type, actor_label, timestamp, details_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (shipment_id, event_type, actor_label, now_iso, details_str),
        )

    if conn is not None:
        _insert(conn)
    else:
        with get_connection() as c:
            _insert(c)

def get_audit_events_for_shipment(shipment_id: str):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, shipment_id, event_type, actor_label, timestamp, details_json
            FROM audit_events
            WHERE shipment_id = ?
            ORDER BY id ASC
            """,
            (shipment_id,),
        ).fetchall()
        return [
            {
                "id": r["id"],
                "shipment_id": r["shipment_id"],
                "event_type": r["event_type"],
                "actor_label": r["actor_label"],
                "timestamp": r["timestamp"],
                "details": json.loads(r["details_json"]) if r["details_json"] else {},
            }
            for r in rows
        ]
