import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from backend.app.models.database import get_connection
from backend.app.schemas.shipment import (
    ShipmentCreateRequest,
    ShipmentResponse,
    SensorResponse,
)
from backend.app.services.profile_service import get_profile_by_id
from backend.app.services.audit_service import record_audit_event

def _generate_sensor_positions(sensor_count: int) -> List[Tuple[str, float, float, float]]:
    """Generates distinct 3D positions and labels for virtual sensors in the package."""
    presets = [
        ("Sensor-1 (Core Center)", 0.0, 0.2, 0.0),
        ("Sensor-2 (Upper Lid)", 0.0, 0.8, 0.0),
        ("Sensor-3 (Bottom Base)", 0.0, -0.6, 0.0),
        ("Sensor-4 (Front Wall)", 0.0, 0.0, 1.2),
        ("Sensor-5 (Rear Wall)", 0.0, 0.0, -1.2),
        ("Sensor-6 (Left Flank)", -1.2, 0.0, 0.0),
        ("Sensor-7 (Right Flank)", 1.2, 0.0, 0.0),
        ("Sensor-8 (Top Corner)", 1.0, 0.7, 1.0),
        ("Sensor-9 (Bottom Corner)", -1.0, -0.6, -1.0),
        ("Sensor-10 (Perimeter)", -0.8, 0.4, 0.8),
    ]
    result = []
    for i in range(sensor_count):
        if i < len(presets):
            result.append(presets[i])
        else:
            angle = (i * 0.7)
            result.append((f"Sensor-{i+1} (Virtual Aux)", 0.9 * (i % 2), 0.1 * i, 0.5))
    return result

def create_shipment(req: ShipmentCreateRequest) -> ShipmentResponse:
    profile = get_profile_by_id(req.profile_id)
    if not profile:
        raise ValueError(f"Product profile '{req.profile_id}' not found.")

    shipment_id = f"shp_{uuid.uuid4().hex[:8]}"
    now_iso = datetime.now(timezone.utc).isoformat()
    status = "created"

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO shipments (
                id, profile_id, status, vial_count, sensor_count,
                destination_label, scenario, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                shipment_id,
                req.profile_id,
                status,
                req.vial_count,
                req.sensor_count,
                req.destination_label,
                req.scenario,
                now_iso,
                now_iso,
            ),
        )

        sensor_configs = _generate_sensor_positions(req.sensor_count)
        for idx, (label, x, y, z) in enumerate(sensor_configs):
            sensor_id = f"{shipment_id}-sn{idx+1}"
            conn.execute(
                """
                INSERT INTO sensors (
                    id, shipment_id, label, position_x, position_y, position_z,
                    health_status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, 'healthy', ?)
                """,
                (sensor_id, shipment_id, label, x, y, z, now_iso),
            )

    record_audit_event(
        event_type="shipment.created",
        shipment_id=shipment_id,
        details={
            "profile_id": req.profile_id,
            "vial_count": req.vial_count,
            "sensor_count": req.sensor_count,
            "scenario": req.scenario,
        },
    )

    return get_shipment_by_id(shipment_id)

def get_shipment_by_id(shipment_id: str) -> Optional[ShipmentResponse]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM shipments WHERE id = ?", (shipment_id,)
        ).fetchone()
        if not row:
            return None

        sensor_rows = conn.execute(
            "SELECT * FROM sensors WHERE shipment_id = ? ORDER BY id ASC",
            (shipment_id,),
        ).fetchall()

        alerts_count_row = conn.execute(
            "SELECT COUNT(*) as cnt FROM alerts WHERE shipment_id = ? AND status = 'active'",
            (shipment_id,),
        ).fetchone()
        active_alerts_count = alerts_count_row["cnt"] if alerts_count_row else 0

    profile = get_profile_by_id(row["profile_id"])
    sensors = [SensorResponse(**dict(s)) for s in sensor_rows]

    return ShipmentResponse(
        id=row["id"],
        profile_id=row["profile_id"],
        status=row["status"],
        vial_count=row["vial_count"],
        sensor_count=row["sensor_count"],
        destination_label=row["destination_label"],
        scenario=row["scenario"],
        started_at=row["started_at"],
        ended_at=row["ended_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        operator_review_status=row["operator_review_status"],
        operator_review_note=row["operator_review_note"],
        profile=profile,
        sensors=sensors,
        active_alerts_count=active_alerts_count,
    )

def list_shipments(
    status: Optional[str] = None,
    profile_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[ShipmentResponse]:
    query = "SELECT id FROM shipments WHERE 1=1"
    params = []
    if status:
        query += " AND status = ?"
        params.append(status)
    if profile_id:
        query += " AND profile_id = ?"
        params.append(profile_id)

    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()

    shipments = []
    for r in rows:
        shp = get_shipment_by_id(r["id"])
        if shp:
            shipments.append(shp)
    return shipments

def update_shipment_status(shipment_id: str, new_status: str) -> ShipmentResponse:
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        row = conn.execute("SELECT status, started_at FROM shipments WHERE id = ?", (shipment_id,)).fetchone()
        if not row:
            raise ValueError(f"Shipment '{shipment_id}' not found.")

        current_status = row["status"]
        if current_status == "completed" and new_status in ("running", "paused"):
            raise ValueError("A completed shipment cannot be resumed or modified.")

        started_at = row["started_at"]
        ended_at = None

        if new_status == "running" and not started_at:
            started_at = now_iso
        elif new_status == "completed":
            ended_at = now_iso

        if ended_at:
            conn.execute(
                """
                UPDATE shipments
                SET status = ?, started_at = coalesce(started_at, ?), ended_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (new_status, started_at, ended_at, now_iso, shipment_id),
            )
        else:
            conn.execute(
                """
                UPDATE shipments
                SET status = ?, started_at = coalesce(started_at, ?), updated_at = ?
                WHERE id = ?
                """,
                (new_status, started_at, now_iso, shipment_id),
            )

    record_audit_event(
        event_type=f"shipment.status_{new_status}",
        shipment_id=shipment_id,
        details={"previous_status": current_status, "new_status": new_status},
    )

    return get_shipment_by_id(shipment_id)

def update_shipment_scenario(shipment_id: str, scenario: str) -> ShipmentResponse:
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute(
            "UPDATE shipments SET scenario = ?, updated_at = ? WHERE id = ?",
            (scenario, now_iso, shipment_id),
        )
    record_audit_event(
        event_type="shipment.scenario_changed",
        shipment_id=shipment_id,
        details={"scenario": scenario},
    )
    return get_shipment_by_id(shipment_id)
