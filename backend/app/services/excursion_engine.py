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

def classify_temperature_grade(temperature_c: float, lower_limit_c: float, upper_limit_c: float) -> tuple:
    """
    Classifies a raw temperature reading into a standardized excursion grade:
    - Grade 0: Within [lower_limit_c, upper_limit_c] -> Normal
    - Grade 1: > 0°C up to 2.0°C beyond limit -> Mild excursion
    - Grade 2: > 2.0°C up to 5.0°C beyond limit -> Moderate excursion
    - Grade 3: > 5.0°C beyond limit -> Severe excursion
    Returns: (direction, grade, delta_c) where direction in ('normal', 'heat', 'cold')
    """
    if temperature_c is None:
        return ("normal", 0, 0.0)

    if temperature_c > upper_limit_c:
        delta = round(temperature_c - upper_limit_c, 3)
        if delta <= 2.0:
            return ("heat", 1, delta)
        elif delta <= 5.0:
            return ("heat", 2, delta)
        else:
            return ("heat", 3, delta)
    elif temperature_c < lower_limit_c:
        delta = round(lower_limit_c - temperature_c, 3)
        if delta <= 2.0:
            return ("cold", 1, delta)
        elif delta <= 5.0:
            return ("cold", 2, delta)
        else:
            return ("cold", 3, delta)
    else:
        return ("normal", 0, 0.0)

def extract_shipment_excursion_features(
    shipment_id: Optional[str] = None,
    lower_limit_c: float = 2.0,
    upper_limit_c: float = 8.0,
    biological_type: str = "monoclonal_antibody",
    excursion_events: Optional[List[Dict[str, Any]]] = None,
    tick_duration_seconds: float = 1.5,
) -> Dict[str, Any]:
    """
    Transforms raw temperature readings and excursion events into the exact
    excursion-grade duration (in seconds) and event count features required by
    the trained scikit-learn viability ML model.
    """
    excursions = excursion_events
    if excursions is None and shipment_id:
        excursions = get_excursion_events_for_shipment(shipment_id)
    if excursions is None:
        excursions = []

    excursion_count = len(excursions)
    heat_excursion_count = sum(1 for e in excursions if e.get("direction") == "upper")
    cold_excursion_count = sum(1 for e in excursions if e.get("direction") == "lower")
    longest_excursion_sec = max(
        (float(e.get("duration_seconds") or 0.0) for e in excursions),
        default=0.0,
    )

    heat_grade_1_time_sec = 0.0
    heat_grade_2_time_sec = 0.0
    heat_grade_3_time_sec = 0.0
    cold_grade_1_time_sec = 0.0
    cold_grade_2_time_sec = 0.0
    cold_grade_3_time_sec = 0.0
    max_grade_reached = 0

    readings_processed = False
    if shipment_id:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT timestamp, temperature_c, sensor_id
                FROM readings
                WHERE shipment_id = ? AND quality_status = 'valid' AND temperature_c IS NOT NULL
                ORDER BY timestamp ASC
                """,
                (shipment_id,),
            ).fetchall()

        if rows:
            readings_processed = True
            # Group readings by timestamp (each tick interval)
            ticks: Dict[str, List[float]] = {}
            for r in rows:
                ts = r["timestamp"]
                t_val = r["temperature_c"]
                ticks.setdefault(ts, []).append(t_val)

            for ts, temps in ticks.items():
                worst_dir = "normal"
                worst_grade = 0
                for temp in temps:
                    direction, grade, _ = classify_temperature_grade(temp, lower_limit_c, upper_limit_c)
                    if grade > worst_grade:
                        worst_grade = grade
                        worst_dir = direction

                if worst_grade > max_grade_reached:
                    max_grade_reached = worst_grade

                if worst_grade == 1:
                    if worst_dir == "heat":
                        heat_grade_1_time_sec += tick_duration_seconds
                    else:
                        cold_grade_1_time_sec += tick_duration_seconds
                elif worst_grade == 2:
                    if worst_dir == "heat":
                        heat_grade_2_time_sec += tick_duration_seconds
                    else:
                        cold_grade_2_time_sec += tick_duration_seconds
                elif worst_grade == 3:
                    if worst_dir == "heat":
                        heat_grade_3_time_sec += tick_duration_seconds
                    else:
                        cold_grade_3_time_sec += tick_duration_seconds

    # If no database readings were available (e.g. standalone test or synthetic excursion list),
    # construct grade times from excursion event records directly
    if not readings_processed and excursions:
        for exc in excursions:
            dur = float(exc.get("duration_seconds") or 0.0)
            direction = exc.get("direction")
            peak = exc.get("peak_temperature_c")
            min_t = exc.get("minimum_temperature_c")

            ref_temp = peak if direction == "upper" else (min_t if min_t is not None else peak)
            if ref_temp is not None:
                _, grade, _ = classify_temperature_grade(ref_temp, lower_limit_c, upper_limit_c)
            else:
                grade = 1

            if grade > max_grade_reached:
                max_grade_reached = grade

            if direction == "upper":
                if grade == 1:
                    heat_grade_1_time_sec += dur
                elif grade == 2:
                    heat_grade_2_time_sec += dur
                else:
                    heat_grade_3_time_sec += dur
            else:
                if grade == 1:
                    cold_grade_1_time_sec += dur
                elif grade == 2:
                    cold_grade_2_time_sec += dur
                else:
                    cold_grade_3_time_sec += dur

    grade_1_time_sec = round(heat_grade_1_time_sec + cold_grade_1_time_sec, 2)
    grade_2_time_sec = round(heat_grade_2_time_sec + cold_grade_2_time_sec, 2)
    grade_3_time_sec = round(heat_grade_3_time_sec + cold_grade_3_time_sec, 2)
    total_excursion_time_sec = round(grade_1_time_sec + grade_2_time_sec + grade_3_time_sec, 2)

    return {
        "biological_type": biological_type,
        "heat_grade_1_time_sec": round(heat_grade_1_time_sec, 2),
        "heat_grade_2_time_sec": round(heat_grade_2_time_sec, 2),
        "heat_grade_3_time_sec": round(heat_grade_3_time_sec, 2),
        "cold_grade_1_time_sec": round(cold_grade_1_time_sec, 2),
        "cold_grade_2_time_sec": round(cold_grade_2_time_sec, 2),
        "cold_grade_3_time_sec": round(cold_grade_3_time_sec, 2),
        "grade_1_time_sec": grade_1_time_sec,
        "grade_2_time_sec": grade_2_time_sec,
        "grade_3_time_sec": grade_3_time_sec,
        "excursion_count": excursion_count,
        "heat_excursion_count": heat_excursion_count,
        "cold_excursion_count": cold_excursion_count,
        "total_excursion_time_sec": total_excursion_time_sec,
        "longest_excursion_sec": round(longest_excursion_sec, 2),
        "max_grade_reached": max_grade_reached,
    }
