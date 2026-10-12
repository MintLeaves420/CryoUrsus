import uuid
import sqlite3
from datetime import datetime, timezone
from typing import List, Optional
from backend.app.models.database import get_connection
from backend.app.schemas.alert import AlertResponse
from backend.app.services.audit_service import record_audit_event

def create_or_update_alert(
    shipment_id: str,
    alert_type: str,
    severity: str,
    title: str,
    message: str,
    sensor_id: Optional[str] = None,
    excursion_event_id: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> AlertResponse:
    now_iso = datetime.now(timezone.utc).isoformat()

    def _run(c: sqlite3.Connection):
        query = """
            SELECT * FROM alerts
            WHERE shipment_id = ? AND type = ? AND status = 'active'
        """
        params = [shipment_id, alert_type]
        if sensor_id:
            query += " AND sensor_id = ?"
            params.append(sensor_id)
        else:
            query += " AND sensor_id IS NULL"

        existing = c.execute(query, params).fetchone()
        if existing:
            c.execute(
                """
                UPDATE alerts
                SET message = ?, severity = ?, updated_at = ?
                WHERE id = ?
                """,
                (message, severity, now_iso, existing["id"]),
            )
            alert_id = existing["id"]
        else:
            alert_id = f"alt_{uuid.uuid4().hex[:8]}"
            c.execute(
                """
                INSERT INTO alerts (
                    id, shipment_id, sensor_id, excursion_event_id,
                    type, severity, status, title, message,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, ?)
                """,
                (
                    alert_id,
                    shipment_id,
                    sensor_id,
                    excursion_event_id,
                    alert_type,
                    severity,
                    title,
                    message,
                    now_iso,
                    now_iso,
                ),
            )
            record_audit_event(
                event_type="alert.created",
                shipment_id=shipment_id,
                details={
                    "alert_id": alert_id,
                    "type": alert_type,
                    "severity": severity,
                    "title": title,
                },
                conn=c,
            )

        row = c.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,)).fetchone()
        return AlertResponse(**dict(row))

    if conn is not None:
        return _run(conn)
    with get_connection() as c:
        return _run(c)

def resolve_alert(alert_id: str, conn: Optional[sqlite3.Connection] = None) -> Optional[AlertResponse]:
    now_iso = datetime.now(timezone.utc).isoformat()

    def _run(c: sqlite3.Connection):
        row = c.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,)).fetchone()
        if not row:
            return None
        c.execute(
            "UPDATE alerts SET status = 'resolved', updated_at = ? WHERE id = ?",
            (now_iso, alert_id),
        )
        updated = c.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,)).fetchone()
        record_audit_event(
            event_type="alert.resolved",
            shipment_id=row["shipment_id"],
            details={"alert_id": alert_id},
            conn=c,
        )
        return AlertResponse(**dict(updated))

    if conn is not None:
        return _run(conn)
    with get_connection() as c:
        return _run(c)

def acknowledge_alert(alert_id: str, acknowledged_by: str = "operator") -> Optional[AlertResponse]:
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,)).fetchone()
        if not row:
            return None
        conn.execute(
            "UPDATE alerts SET status = 'acknowledged', acknowledged_at = ?, updated_at = ? WHERE id = ?",
            (now_iso, now_iso, alert_id),
        )
        updated = conn.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,)).fetchone()
        record_audit_event(
            event_type="alert.acknowledged",
            shipment_id=row["shipment_id"],
            actor_label=acknowledged_by,
            details={"alert_id": alert_id},
        )
        return AlertResponse(**dict(updated))

def list_alerts(
    shipment_id: Optional[str] = None,
    status: Optional[str] = None,
) -> List[AlertResponse]:
    query = "SELECT * FROM alerts WHERE 1=1"
    params = []
    if shipment_id:
        query += " AND shipment_id = ?"
        params.append(shipment_id)
    if status:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY created_at DESC"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        return [AlertResponse(**dict(r)) for r in rows]
