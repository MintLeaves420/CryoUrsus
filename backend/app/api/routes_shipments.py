import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from backend.app.schemas.shipment import (
    ShipmentCreateRequest,
    ShipmentScenarioUpdateRequest,
    ShipmentResponse,
)
from backend.app.schemas.summary import ShipmentSummaryResponse
from backend.app.schemas.assessment import AssessmentCreateRequest, AssessmentResponse
from backend.app.schemas.nfc import NFCTransferResponse
from backend.app.services.shipment_service import (
    create_shipment,
    get_shipment_by_id,
    list_shipments,
    update_shipment_scenario,
)
from backend.app.services.simulation_service import simulation_service
from backend.app.services.excursion_engine import get_excursion_events_for_shipment
from backend.app.services.viability_estimator import calculate_demo_viability
from backend.app.services.audit_service import get_audit_events_for_shipment, record_audit_event
from backend.app.services.nfc_service import trigger_simulated_nfc_transfer
from backend.app.services.report_service import generate_shipment_pdf
from backend.app.models.database import get_connection
from backend.app.config import METHOD_VERSION, DEMO_DISCLAIMER
from backend.app.api.websocket import ws_manager

router = APIRouter(prefix="/shipments", tags=["Shipments"])

@router.get("", response_model=List[ShipmentResponse])
def get_all_shipments(
    status: Optional[str] = Query(default=None),
    profile_id: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    return list_shipments(status=status, profile_id=profile_id, limit=limit, offset=offset)

@router.post("", response_model=ShipmentResponse, status_code=201)
def create_new_shipment(req: ShipmentCreateRequest):
    try:
        return create_shipment(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": {"code": "bad_request", "message": str(e)}})

@router.get("/{shipment_id}", response_model=ShipmentResponse)
def get_single_shipment(shipment_id: str):
    shp = get_shipment_by_id(shipment_id)
    if not shp:
        raise HTTPException(status_code=404, detail={"error": {"code": "not_found", "message": f"Shipment '{shipment_id}' not found."}})
    return shp

@router.post("/{shipment_id}/start", response_model=ShipmentResponse)
async def start_shipment_simulation(shipment_id: str):
    shp = get_shipment_by_id(shipment_id)
    if not shp:
        raise HTTPException(status_code=404, detail={"error": {"code": "not_found", "message": f"Shipment '{shipment_id}' not found."}})
    if shp.status == "completed":
        raise HTTPException(status_code=409, detail={"error": {"code": "invalid_state", "message": "A completed shipment cannot be restarted."}})

    await simulation_service.start_simulation(shipment_id)
    return get_shipment_by_id(shipment_id)

@router.post("/{shipment_id}/pause", response_model=ShipmentResponse)
async def pause_shipment_simulation(shipment_id: str):
    shp = get_shipment_by_id(shipment_id)
    if not shp:
        raise HTTPException(status_code=404, detail={"error": {"code": "not_found", "message": f"Shipment '{shipment_id}' not found."}})
    if shp.status == "completed":
        raise HTTPException(status_code=409, detail={"error": {"code": "invalid_state", "message": "A completed shipment cannot be modified."}})

    await simulation_service.pause_simulation(shipment_id)
    return get_shipment_by_id(shipment_id)

@router.post("/{shipment_id}/resume", response_model=ShipmentResponse)
async def resume_shipment_simulation(shipment_id: str):
    shp = get_shipment_by_id(shipment_id)
    if not shp:
        raise HTTPException(status_code=404, detail={"error": {"code": "not_found", "message": f"Shipment '{shipment_id}' not found."}})
    if shp.status == "completed":
        raise HTTPException(status_code=409, detail={"error": {"code": "invalid_state", "message": "A completed shipment cannot be resumed."}})

    await simulation_service.resume_simulation(shipment_id)
    return get_shipment_by_id(shipment_id)

@router.post("/{shipment_id}/end", response_model=ShipmentResponse)
async def end_shipment_simulation(shipment_id: str):
    shp = get_shipment_by_id(shipment_id)
    if not shp:
        raise HTTPException(status_code=404, detail={"error": {"code": "not_found", "message": f"Shipment '{shipment_id}' not found."}})

    await simulation_service.end_simulation(shipment_id)
    return get_shipment_by_id(shipment_id)

@router.post("/{shipment_id}/scenario", response_model=ShipmentResponse)
def set_shipment_scenario(shipment_id: str, req: ShipmentScenarioUpdateRequest):
    valid_scenarios = [
        "normal",
        "gradual_warming",
        "gradual_cooling",
        "sudden_spike",
        "sudden_drop",
        "repeated_fluctuations",
        "stuck",
        "disconnected",
        "implausible",
    ]
    if req.scenario not in valid_scenarios:
        raise HTTPException(status_code=400, detail={
            "error": {"code": "invalid_scenario", "message": f"Scenario must be one of: {', '.join(valid_scenarios)}"}
        })

    shp = get_shipment_by_id(shipment_id)
    if not shp:
        raise HTTPException(status_code=404, detail={"error": {"code": "not_found", "message": f"Shipment '{shipment_id}' not found."}})

    return update_shipment_scenario(shipment_id, req.scenario)

@router.get("/{shipment_id}/summary", response_model=ShipmentSummaryResponse)
def get_shipment_summary(shipment_id: str):
    shp = get_shipment_by_id(shipment_id)
    if not shp:
        raise HTTPException(status_code=404, detail={"error": {"code": "not_found", "message": f"Shipment '{shipment_id}' not found."}})

    with get_connection() as conn:
        stats = conn.execute(
            """
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN quality_status = 'valid' THEN 1 END) as valid_cnt,
                   MAX(temperature_c) as max_temp,
                   MIN(temperature_c) as min_temp
            FROM readings WHERE shipment_id = ?
            """,
            (shipment_id,),
        ).fetchone()

        sensor_rows = conn.execute(
            "SELECT id, label, health_status, last_valid_temperature_c, last_reading_at FROM sensors WHERE shipment_id = ?",
            (shipment_id,),
        ).fetchall()

    total_cnt = stats["total"] or 0
    valid_cnt = stats["valid_cnt"] or 0
    max_t = stats["max_temp"]
    min_t = stats["min_temp"]

    excursions = get_excursion_events_for_shipment(shipment_id)
    total_exc_duration = sum((e.get("duration_seconds") or 0.0) for e in excursions)

    # Estimate viability and explainability
    params = {}
    if shp.profile and shp.profile.demo_parameters_json:
        try:
            params = json.loads(shp.profile.demo_parameters_json)
        except Exception:
            pass

    viability = calculate_demo_viability(
        valid_readings_count=valid_cnt,
        total_readings=total_cnt,
        excursion_events=excursions,
        demo_parameters=params,
    )

    coverage = valid_cnt / total_cnt if total_cnt > 0 else 0.0
    quality_status = "Optimal Telemetry" if coverage >= 0.95 else ("Degraded Telemetry" if coverage >= 0.50 else "Critical Telemetry Loss")

    return ShipmentSummaryResponse(
        shipment_id=shipment_id,
        status=shp.status,
        total_readings=total_cnt,
        valid_readings_count=valid_cnt,
        valid_data_coverage=round(coverage, 3),
        peak_temperature_c=max_t,
        minimum_temperature_c=min_t,
        excursion_duration_seconds=round(total_exc_duration, 1),
        crossing_count=len(excursions),
        max_rate_c_per_minute=0.0,
        data_quality_status=quality_status,
        sensors_summary=[dict(s) for s in sensor_rows],
        demo_score=viability["score"],
        demo_label=viability["label"],
        explanation=viability["explanation"],
        method_version=METHOD_VERSION,
        disclaimer=DEMO_DISCLAIMER,
    )

@router.get("/{shipment_id}/events")
def get_shipment_events(shipment_id: str):
    shp = get_shipment_by_id(shipment_id)
    if not shp:
        raise HTTPException(status_code=404, detail={"error": {"code": "not_found", "message": f"Shipment '{shipment_id}' not found."}})

    excursions = get_excursion_events_for_shipment(shipment_id)
    audits = get_audit_events_for_shipment(shipment_id)

    return {
        "shipment_id": shipment_id,
        "excursion_events": excursions,
        "audit_events": audits,
    }

@router.get("/{shipment_id}/assessment", response_model=AssessmentResponse)
def get_shipment_assessment(shipment_id: str):
    shp = get_shipment_by_id(shipment_id)
    if not shp:
        raise HTTPException(status_code=404, detail={"error": {"code": "not_found", "message": f"Shipment '{shipment_id}' not found."}})

    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM assessments WHERE shipment_id = ? ORDER BY created_at DESC LIMIT 1",
            (shipment_id,),
        ).fetchone()

        stats = conn.execute(
            """
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN quality_status = 'valid' THEN 1 END) as valid_cnt
            FROM readings WHERE shipment_id = ?
            """,
            (shipment_id,),
        ).fetchone()

    total_cnt = stats["total"] or 0
    valid_cnt = stats["valid_cnt"] or 0
    excursions = get_excursion_events_for_shipment(shipment_id)

    viability = calculate_demo_viability(
        valid_readings_count=valid_cnt,
        total_readings=total_cnt,
        excursion_events=excursions,
    )

    if row:
        return AssessmentResponse(
            id=row["id"],
            shipment_id=shipment_id,
            review_status=row["review_status"],
            review_note=row["review_note"],
            reviewer_label=row["reviewer_label"],
            created_at=row["created_at"],
            method_version=row["method_version"] or METHOD_VERSION,
            demo_score=row["demo_score"] if row["demo_score"] is not None else viability["score"],
            demo_label=row["demo_label"] or viability["label"],
            features=json.loads(row["features_json"]) if row["features_json"] else viability["features"],
            explanation=json.loads(row["explanation_json"]) if row["explanation_json"] else viability["explanation"],
            disclaimer=row["disclaimer"] or DEMO_DISCLAIMER,
        )

    return AssessmentResponse(
        shipment_id=shipment_id,
        review_status=shp.operator_review_status or "pending",
        review_note=shp.operator_review_note,
        reviewer_label=None,
        method_version=METHOD_VERSION,
        demo_score=viability["score"],
        demo_label=viability["label"],
        features=viability["features"],
        explanation=viability["explanation"],
        disclaimer=DEMO_DISCLAIMER,
    )

@router.post("/{shipment_id}/assessment", response_model=AssessmentResponse)
async def submit_shipment_assessment(shipment_id: str, req: AssessmentCreateRequest):
    shp = get_shipment_by_id(shipment_id)
    if not shp:
        raise HTTPException(status_code=404, detail={"error": {"code": "not_found", "message": f"Shipment '{shipment_id}' not found."}})

    with get_connection() as conn:
        stats = conn.execute(
            """
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN quality_status = 'valid' THEN 1 END) as valid_cnt
            FROM readings WHERE shipment_id = ?
            """,
            (shipment_id,),
        ).fetchone()

    total_cnt = stats["total"] or 0
    valid_cnt = stats["valid_cnt"] or 0
    excursions = get_excursion_events_for_shipment(shipment_id)

    viability = calculate_demo_viability(
        valid_readings_count=valid_cnt,
        total_readings=total_cnt,
        excursion_events=excursions,
    )

    assessment_id = f"asm_{uuid.uuid4().hex[:8]}"
    now_iso = datetime.now(timezone.utc).isoformat()

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO assessments (
                id, shipment_id, review_status, review_note, reviewer_label,
                created_at, method_version, demo_score, demo_label,
                features_json, explanation_json, disclaimer
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                assessment_id,
                shipment_id,
                req.review_status,
                req.review_note,
                req.reviewer_label,
                now_iso,
                METHOD_VERSION,
                viability["score"],
                viability["label"],
                json.dumps(viability["features"]),
                json.dumps(viability["explanation"]),
                DEMO_DISCLAIMER,
            ),
        )

        conn.execute(
            """
            UPDATE shipments
            SET operator_review_status = ?, operator_review_note = ?, updated_at = ?
            WHERE id = ?
            """,
            (req.review_status, req.review_note, now_iso, shipment_id),
        )

    record_audit_event(
        event_type="assessment.updated",
        shipment_id=shipment_id,
        actor_label=req.reviewer_label or "operator",
        details={
            "assessment_id": assessment_id,
            "review_status": req.review_status,
            "demo_score": viability["score"],
        },
    )

    await ws_manager.broadcast(shipment_id, {
        "type": "assessment.updated",
        "version": 1,
        "shipment_id": shipment_id,
        "timestamp": now_iso,
        "data": {
            "review_status": req.review_status,
            "review_note": req.review_note,
            "demo_score": viability["score"],
        },
    })

    return AssessmentResponse(
        id=assessment_id,
        shipment_id=shipment_id,
        review_status=req.review_status,
        review_note=req.review_note,
        reviewer_label=req.reviewer_label,
        created_at=now_iso,
        method_version=METHOD_VERSION,
        demo_score=viability["score"],
        demo_label=viability["label"],
        features=viability["features"],
        explanation=viability["explanation"],
        disclaimer=DEMO_DISCLAIMER,
    )

@router.post("/{shipment_id}/nfc-transfer", response_model=NFCTransferResponse)
async def post_nfc_transfer(shipment_id: str):
    try:
        res = trigger_simulated_nfc_transfer(shipment_id)
        await ws_manager.broadcast(shipment_id, {
            "type": "nfc.transfer_updated",
            "version": 1,
            "shipment_id": shipment_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": res.model_dump(),
        })
        return res
    except ValueError as e:
        raise HTTPException(status_code=404, detail={"error": {"code": "not_found", "message": str(e)}})

@router.get("/{shipment_id}/report.pdf")
def download_shipment_report(shipment_id: str):
    try:
        pdf_stream = generate_shipment_pdf(shipment_id)
        record_audit_event(
            event_type="report.generated",
            shipment_id=shipment_id,
            details={"format": "PDF"},
        )
        return StreamingResponse(
            pdf_stream,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="cryoursus_{shipment_id}_report.pdf"'
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail={"error": {"code": "not_found", "message": str(e)}})
