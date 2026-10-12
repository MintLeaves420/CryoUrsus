import json
from typing import Dict, Any, Optional, List
from backend.app.config import METHOD_VERSION, DEMO_DISCLAIMER

MIN_VALID_COVERAGE_THRESHOLD = 0.50

def calculate_demo_viability(
    valid_readings_count: int,
    total_readings: int,
    excursion_events: List[Dict[str, Any]],
    demo_parameters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Deterministic, transparent illustrative estimator for cold-chain simulation demo.
    Strictly marked as illustrative hackathon demo; never claims real product potency.
    """
    if total_readings == 0:
        return {
            "status": "insufficient_data",
            "score": None,
            "label": "Insufficient Telemetry Data",
            "features": {
                "valid_data_coverage": 0.0,
                "total_readings": 0,
                "valid_readings_count": 0,
                "exposure_degree_minutes": 0.0,
                "crossing_count": 0,
                "upper_breach_seconds": 0.0,
                "lower_breach_seconds": 0.0,
            },
            "explanation": [
                "No telemetry readings have been received for this shipment yet.",
                "Demo estimator requires active sensor streaming.",
            ],
            "method_version": METHOD_VERSION,
            "disclaimer": DEMO_DISCLAIMER,
        }

    coverage = valid_readings_count / total_readings

    if coverage < MIN_VALID_COVERAGE_THRESHOLD:
        return {
            "status": "insufficient_data",
            "score": None,
            "label": "Insufficient Trustworthy Data",
            "features": {
                "valid_data_coverage": round(coverage, 2),
                "total_readings": total_readings,
                "valid_readings_count": valid_readings_count,
                "exposure_degree_minutes": 0.0,
                "crossing_count": 0,
                "upper_breach_seconds": 0.0,
                "lower_breach_seconds": 0.0,
            },
            "explanation": [
                f"Valid data coverage is only {coverage*100:.1f}%, which is below the 50% reliability threshold.",
                "Sensor dropouts, stuck values, or implausible readings prevent a trustworthy demo estimate.",
            ],
            "method_version": METHOD_VERSION,
            "disclaimer": DEMO_DISCLAIMER,
        }

    # Extract features from excursion events
    total_exposure_deg_min = 0.0
    upper_seconds = 0.0
    lower_seconds = 0.0
    crossing_count = len(excursion_events)

    for exc in excursion_events:
        exposure = exc.get("exposure_degree_minutes") or 0.0
        total_exposure_deg_min += exposure
        duration = exc.get("duration_seconds") or 0.0
        if exc.get("direction") == "upper":
            upper_seconds += duration
        else:
            lower_seconds += duration

    params = demo_parameters or {}
    decay_rate = params.get("decay_rate_per_deg_min", 0.8)

    # Compute deterministic score
    if crossing_count == 0 or total_exposure_deg_min <= 0.0:
        score = 100.0
        label = "Optimal Thermal Stability (Illustrative Demo)"
        explanation_lines = [
            "All sensor readings remained continuously within the configured storage envelope.",
            "No thermal breaches or cumulative heat loads observed.",
            f"Sensor telemetry coverage: {coverage*100:.1f}%.",
        ]
    else:
        # Transparent formula: 100 - (exposure_degree_minutes * decay_rate + (crossing_count - 1) * 1.5)
        penalty = (total_exposure_deg_min * decay_rate) + (max(0, crossing_count - 1) * 1.5)
        raw_score = max(10.0, 100.0 - penalty)
        score = round(raw_score, 1)

        if score >= 90.0:
            label = "Minor Thermal Exposure (Illustrative Demo)"
        elif score >= 70.0:
            label = "Moderate Thermal Degradation (Illustrative Demo)"
        else:
            label = "Significant Excursion Impact (Illustrative Demo)"

        explanation_lines = [
            f"Recorded {crossing_count} thermal excursion event(s) totaling {total_exposure_deg_min:.2f} degree-minutes.",
            f"Upper limit breach time: {upper_seconds:.0f}s; Lower limit breach time: {lower_seconds:.0f}s.",
            f"Deterministic penalty of {penalty:.1f} points applied using model profile '{METHOD_VERSION}'.",
        ]

    explanation_lines.append(
        "Notice: This score is a mathematical demonstration for hackathon evaluation and does not represent verified biologic potency."
    )

    return {
        "status": "demo_estimate",
        "score": score,
        "label": label,
        "features": {
            "valid_data_coverage": round(coverage, 3),
            "total_readings": total_readings,
            "valid_readings_count": valid_readings_count,
            "exposure_degree_minutes": round(total_exposure_deg_min, 2),
            "crossing_count": crossing_count,
            "upper_breach_seconds": round(upper_seconds, 1),
            "lower_breach_seconds": round(lower_seconds, 1),
        },
        "explanation": explanation_lines,
        "method_version": METHOD_VERSION,
        "disclaimer": DEMO_DISCLAIMER,
    }
