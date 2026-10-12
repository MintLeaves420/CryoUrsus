import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from backend.app.models.database import get_connection
from backend.app.services.alert_service import create_or_update_alert, resolve_alert
from backend.app.services.audit_service import record_audit_event

def _parse_iso(iso_str: str) -> datetime:
    return datetime.fromisoformat(iso_str)

def process_reading_for_excursions(
    shipment_id: str,
    sensor_id: str,
    temperature_c: float,
    lower_limit_c: float,
    upper_limit_c: float,
    timestamp_iso: str,
    tick_duration_seconds: float = 1.5,
) -> Optional[Dict[str, Any]]:
    """
    Evaluates a single trustworthy temperature reading against configured thermal thresholds.
    Tracks active excursion lifecycle, updates continuous duration/exposure, and triggers alerts.
    """
    now_dt = _parse_iso(timestamp_iso)
    tick_minutes = tick_duration_seconds / 60.0

    breach_direction = None
    if temperature_c > upper_limit_c:
        breach_direction = "upper"
    elif temperature_c < lower_limit_c:
        breach_direction = "lower"

    with get_connection() as conn:
        # Check if this sensor already has an active excursion
        active_excursions = conn.execute(
            """
            SELECT * FROM excursion_events
            WHERE shipment_id = ? AND sensor_id = ? AND status = 'active'
            """,
            (shipment_id, sensor_id),
        ).fetchall()

        if breach_direction:
            # Check if active excursion matches current breach direction
            matching = next((e for e in active_excursions if e["direction"] == breach_direction), None)

            if matching:
                # Update existing continuous event
                start_dt = _parse_iso(matching["started_at"])
                duration_sec = max(0.0, (now_dt - start_dt).total_seconds())

                new_peak = max(matching["peak_temperature_c"] or temperature_c, temperature_c)
                new_min = min(matching["minimum_temperature_c"] or temperature_c, temperature_c)

                limit_val = upper_limit_c if breach_direction == "upper" else lower_limit_c
                delta_deg = abs(temperature_c - limit_val)
                current_exp = matching["exposure_degree_minutes"] or 0.0
                new_exposure = current_exp + (delta_deg * tick_minutes)

                conn.execute(
                    """
                    UPDATE excursion_events
                    SET last_breach_at = ?, duration_seconds = ?,
                        peak_temperature_c = ?, minimum_temperature_c = ?,
                        exposure_degree_minutes = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        timestamp_iso,
                        duration_sec,
                        new_peak,
                        new_min,
                        new_exposure,
                        timestamp_iso,
                        matching["id"],
                    ),
                )

                # Keep alert updated with latest peak and duration
                alert_type = f"{breach_direction}_limit"
                severity = "critical" if duration_sec > 30 else "warning"
                create_or_update_alert(
                    shipment_id=shipment_id,
                    alert_type=alert_type,
                    severity=severity,
                    title=f"Temperature Breach ({breach_direction.upper()}) on {sensor_id}",
                    message=f"{sensor_id} observed {temperature_c:.1f}°C (Threshold: {limit_val:.1f}°C). Continuous duration: {duration_sec:.0f}s. Peak: {new_peak:.1f}°C.",
                    sensor_id=sensor_id,
                    excursion_event_id=matching["id"],
                    conn=conn,
                )

                return {
                    "event": "excursion_updated",
                    "excursion_id": matching["id"],
                    "direction": breach_direction,
                    "duration_seconds": duration_sec,
                }
            else:
                # If there's an opposite direction active event, resolve it first
                for opposite in active_excursions:
                    _close_excursion(conn, opposite["id"], timestamp_iso, shipment_id)

                # Create new excursion event
                event_id = f"exc_{uuid.uuid4().hex[:8]}"
                limit_val = upper_limit_c if breach_direction == "upper" else lower_limit_c
                delta_deg = abs(temperature_c - limit_val)
                exposure_deg_min = delta_deg * tick_minutes

                conn.execute(
                    """
                    INSERT INTO excursion_events (
                        id, shipment_id, sensor_id, direction, status,
                        started_at, last_breach_at, duration_seconds,
                        peak_temperature_c, minimum_temperature_c, crossing_count,
                        exposure_degree_minutes, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, 'active', ?, ?, 0.0, ?, ?, 1, ?, ?, ?)
                    """,
                    (
                        event_id,
                        shipment_id,
                        sensor_id,
                        breach_direction,
                        timestamp_iso,
                        timestamp_iso,
                        temperature_c,
                        temperature_c,
                        exposure_deg_min,
                        timestamp_iso,
                        timestamp_iso,
                    ),
                )

                alert_type = f"{breach_direction}_limit"
                create_or_update_alert(
                    shipment_id=shipment_id,
                    alert_type=alert_type,
                    severity="warning",
                    title=f"Temperature Breach ({breach_direction.upper()}) on {sensor_id}",
                    message=f"{sensor_id} entered breach at {temperature_c:.1f}°C (Configured Limit: {limit_val:.1f}°C).",
                    sensor_id=sensor_id,
                    excursion_event_id=event_id,
                    conn=conn,
                )

                record_audit_event(
                    event_type="excursion.started",
                    shipment_id=shipment_id,
                    details={
                        "excursion_id": event_id,
                        "sensor_id": sensor_id,
                        "direction": breach_direction,
                        "temperature_c": temperature_c,
                    },
                    conn=conn,
                )

                return {
                    "event": "excursion_started",
                    "excursion_id": event_id,
                    "direction": breach_direction,
                }
        else:
            # Temperature is within safe limits. Resolve any active excursions for this sensor
            resolved_events = []
            for exc in active_excursions:
                _close_excursion(conn, exc["id"], timestamp_iso, shipment_id)
                resolved_events.append(exc["id"])

            if resolved_events:
                return {
                    "event": "excursion_resolved",
                    "excursion_ids": resolved_events,
                }

    return None

def _close_excursion(conn, excursion_id: str, timestamp_iso: str, shipment_id: str) -> None:
    row = conn.execute("SELECT * FROM excursion_events WHERE id = ?", (excursion_id,)).fetchone()
    if not row or row["status"] != "active":
        return

    start_dt = _parse_iso(row["started_at"])
    end_dt = _parse_iso(timestamp_iso)
    duration_sec = max(0.0, (end_dt - start_dt).total_seconds())

    conn.execute(
        """
        UPDATE excursion_events
        SET status = 'resolved', ended_at = ?, duration_seconds = ?, updated_at = ?
        WHERE id = ?
        """,
        (timestamp_iso, duration_sec, timestamp_iso, excursion_id),
    )

    # Find associated active alert and resolve
    alert_row = conn.execute(
        "SELECT id FROM alerts WHERE excursion_event_id = ? AND status = 'active'",
        (excursion_id,),
    ).fetchone()
    if alert_row:
        resolve_alert(alert_row["id"], conn=conn)

    record_audit_event(
        event_type="excursion.ended",
        shipment_id=shipment_id,
        details={
            "excursion_id": excursion_id,
            "duration_seconds": duration_sec,
        },
        conn=conn,
    )

def get_excursion_events_for_shipment(shipment_id: str) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM excursion_events
            WHERE shipment_id = ?
            ORDER BY started_at ASC
            """,
            (shipment_id,),
        ).fetchall()
        return [dict(r) for r in rows]
