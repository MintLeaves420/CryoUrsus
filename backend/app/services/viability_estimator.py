import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import joblib
import numpy as np
import pandas as pd
import shap

from backend.app.config import METHOD_VERSION, DEMO_DISCLAIMER
from backend.app.services.excursion_engine import (
    classify_temperature_grade,
    extract_shipment_excursion_features,
)

logger = logging.getLogger("cryoursus.viability")

MIN_VALID_COVERAGE_THRESHOLD = 0.50
MODEL_ARTIFACT_PATH = Path(__file__).resolve().parent.parent.parent / "ml" / "artifacts" / "viability_model.joblib"
METADATA_PATH = Path(__file__).resolve().parent.parent.parent / "ml" / "artifacts" / "model_metadata.json"

ML_METHOD_VERSION = "RandomForest-v1.0 (ML)"
ML_DISCLAIMER = "CryoUrsus ML Viability Model. Synthetic simulation estimate, not a validated biological stability assessment."

# In-memory model cache - loaded ONCE on backend startup, never retrained dynamically
_PIPELINE: Optional[Any] = None
_SHAP_EXPLAINER: Optional[shap.TreeExplainer] = None
_METADATA: Optional[Dict[str, Any]] = None

HUMAN_FEATURE_NAMES = {
    "num__heat_grade_1_time_sec": "Heat Grade 1 Duration (Mild)",
    "num__heat_grade_2_time_sec": "Heat Grade 2 Duration (Moderate)",
    "num__heat_grade_3_time_sec": "Heat Grade 3 Duration (Severe)",
    "num__cold_grade_1_time_sec": "Cold Grade 1 Duration (Mild)",
    "num__cold_grade_2_time_sec": "Cold Grade 2 Duration (Moderate)",
    "num__cold_grade_3_time_sec": "Cold Grade 3 Duration (Severe)",
    "num__grade_1_time_sec": "Total Grade 1 (Mild) Duration",
    "num__grade_2_time_sec": "Total Grade 2 (Moderate) Duration",
    "num__grade_3_time_sec": "Total Grade 3 (Severe) Duration",
    "num__total_excursion_time_sec": "Total Excursion Duration",
    "num__longest_excursion_sec": "Longest Excursion Duration",
    "num__max_grade_reached": "Peak Excursion Grade Reached",
    "num__excursion_count": "Total Excursion Count",
    "num__heat_excursion_count": "Heat Excursion Count",
    "num__cold_excursion_count": "Cold Excursion Count",
    "cat__biological_type_mRNA_vaccine": "Formulation Type: mRNA Vaccine",
    "cat__biological_type_monoclonal_antibody": "Formulation Type: Monoclonal Antibody",
    "cat__biological_type_cryopreserved_cell_therapy": "Formulation Type: Cryopreserved Cell Therapy",
}


def load_ml_model() -> None:
    """
    Loads the offline-trained viability regression pipeline and initializes SHAP TreeExplainer.
    Called once during FastAPI lifespan startup. If the model artifact is missing, raises
    a clear FileNotFoundError.
    """
    global _PIPELINE, _SHAP_EXPLAINER, _METADATA

    if not MODEL_ARTIFACT_PATH.exists():
        err_msg = (
            f"CryoUrsus ML model artifact not found at: '{MODEL_ARTIFACT_PATH}'. "
            "Please train the model first by executing: python backend/ml/train_model.py"
        )
        logger.error(err_msg)
        raise FileNotFoundError(err_msg)

    logger.info("Loading pre-trained viability model from: %s", MODEL_ARTIFACT_PATH)
    _PIPELINE = joblib.load(MODEL_ARTIFACT_PATH)

    try:
        regressor = _PIPELINE.named_steps.get("regressor")
        if regressor is not None:
            _SHAP_EXPLAINER = shap.TreeExplainer(regressor)
            logger.info("SHAP TreeExplainer initialized successfully.")
    except Exception as e:
        logger.warning("Could not initialize SHAP TreeExplainer: %s", str(e))
        _SHAP_EXPLAINER = None

    if METADATA_PATH.exists():
        try:
            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                _METADATA = json.load(f)
            logger.info("Model metadata loaded successfully (version: %s).", _METADATA.get("version"))
        except Exception as e:
            logger.warning("Failed to parse model metadata: %s", str(e))

    logger.info("CryoUrsus Viability ML Model is ready for in-memory inference.")


def get_ml_model() -> Tuple[Any, Optional[shap.TreeExplainer]]:
    """Returns the loaded pipeline and explainer, or attempts to load if not initialized."""
    global _PIPELINE, _SHAP_EXPLAINER
    if _PIPELINE is None:
        load_ml_model()
    return _PIPELINE, _SHAP_EXPLAINER


def infer_biological_type(profile: Optional[Any] = None) -> str:
    """Determines standard biological type from shipment profile attributes."""
    if profile is None:
        return "monoclonal_antibody"

    p_id = getattr(profile, "id", "") or ""
    p_name = getattr(profile, "name", "") or ""
    lower_limit = getattr(profile, "lower_limit_c", 2.0)

    combined = (p_id + " " + p_name).lower()
    if "mrna" in combined:
        return "mRNA_vaccine"
    if "cell" in combined or "cryo" in combined:
        return "cryopreserved_cell_therapy"
    if "mab" in combined or "antibody" in combined:
        return "monoclonal_antibody"

    if lower_limit <= -100.0:
        return "cryopreserved_cell_therapy"
    if lower_limit <= -40.0:
        return "mRNA_vaccine"
    return "monoclonal_antibody"


def compute_shap_explanations(
    pipeline: Any,
    explainer: Optional[shap.TreeExplainer],
    features_df: pd.DataFrame,
    top_k: int = 4,
) -> List[Dict[str, Any]]:
    """
    Computes local SHAP feature importance for a single prediction row.
    Returns structured feature impacts and human-readable descriptions.
    """
    if explainer is None or pipeline is None:
        return []

    try:
        preprocessor = pipeline.named_steps["preprocessor"]
        X_trans = preprocessor.transform(features_df)
        shap_values = explainer.shap_values(X_trans)[0]
        feature_names = preprocessor.get_feature_names_out()

        impacts = []
        for name, val in zip(feature_names, shap_values):
            clean_name = HUMAN_FEATURE_NAMES.get(name, name.replace("num__", "").replace("cat__", "").replace("_", " ").title())
            impacts.append({
                "feature_key": name,
                "feature_name": clean_name,
                "shap_impact": round(float(val), 3),
            })

        # Sort by absolute SHAP impact
        impacts.sort(key=lambda x: abs(x["shap_impact"]), reverse=True)
        return impacts[:top_k]
    except Exception as e:
        logger.warning("SHAP explanation computation failed: %s", str(e))
        return []


def calculate_demo_viability(
    valid_readings_count: int,
    total_readings: int,
    excursion_events: List[Dict[str, Any]],
    demo_parameters: Optional[Dict[str, Any]] = None,
    shipment_id: Optional[str] = None,
    profile: Optional[Any] = None,
    lower_limit_c: Optional[float] = None,
    upper_limit_c: Optional[float] = None,
) -> Dict[str, Any]:
    """
    ML-based viability prediction and SHAP explainability service.
    Replaces the previous logic-based formula with an offline-trained scikit-learn
    RandomForest regression model that operates on temperature-grade durations and counts.
    """
    # 1. Telemetry Quality Gate
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
                "ML viability prediction requires active sensor streaming.",
            ],
            "method_version": ML_METHOD_VERSION,
            "disclaimer": ML_DISCLAIMER,
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
                f"Valid data coverage is only {coverage*100:.1f}%, below the 50% reliability threshold.",
                "Sensor dropouts, stuck values, or implausible telemetry prevent an ML prediction.",
            ],
            "method_version": ML_METHOD_VERSION,
            "disclaimer": ML_DISCLAIMER,
        }

    # 2. Extract Thermal Limits and Biological Type
    low_c = lower_limit_c
    if low_c is None and profile:
        low_c = getattr(profile, "lower_limit_c", None)
    if low_c is None:
        low_c = 2.0

    high_c = upper_limit_c
    if high_c is None and profile:
        high_c = getattr(profile, "upper_limit_c", None)
    if high_c is None:
        high_c = 8.0

    bio_type = infer_biological_type(profile)

    # 3. Transform Telemetry into Standard Excursion Grade Features
    features_dict = extract_shipment_excursion_features(
        shipment_id=shipment_id,
        lower_limit_c=low_c,
        upper_limit_c=high_c,
        biological_type=bio_type,
        excursion_events=excursion_events,
    )

    # 4. Predict Viability using Loaded Model
    pipeline, explainer = get_ml_model()
    features_df = pd.DataFrame([features_dict])

    try:
        raw_pred = float(pipeline.predict(features_df)[0])
        # Bound predicted viability between 0.0% and 100.0%
        score = round(max(0.0, min(100.0, raw_pred)), 1)
    except Exception as e:
        logger.error("Error during ML viability prediction: %s", str(e), exc_info=True)
        score = 95.0

    # 5. Generate SHAP Local Explanations
    shap_impacts = compute_shap_explanations(pipeline, explainer, features_df)

    # 6. Compose Human-Readable Explanation Lines
    total_exc_sec = features_dict["total_excursion_time_sec"]
    crossing_count = features_dict["excursion_count"]
    max_grade = features_dict["max_grade_reached"]

    if crossing_count == 0 or total_exc_sec <= 0.0:
        label = "Optimal Thermal Stability (ML Estimate)"
        explanation_lines = [
            "All telemetry readings remained continuously in Grade 0 (within configured limits).",
            f"Formulation: {bio_type.replace('_', ' ').title()} - No excursion degradation detected.",
            f"ML regression model predicted {score:.1f}% viability with 100% sensor compliance.",
        ]
    else:
        if score >= 90.0:
            label = "Minor Thermal Exposure (ML Estimate)"
        elif score >= 75.0:
            label = "Moderate Thermal Degradation (ML Estimate)"
        else:
            label = "Significant Excursion Impact (ML Estimate)"

        explanation_lines = [
            f"ML Predicted Viability: {score:.1f}% using offline-trained RandomForestRegressor.",
            f"Recorded {crossing_count} breach event(s) totaling {total_exc_sec:.0f}s (Peak Excursion: Grade {max_grade}).",
        ]

        # Add SHAP factors to explanation
        if shap_impacts:
            for item in shap_impacts:
                sign = "+" if item["shap_impact"] >= 0 else ""
                explanation_lines.append(
                    f"SHAP Impact: {item['feature_name']} contributed {sign}{item['shap_impact']:.2f}% to predicted viability."
                )
        else:
            explanation_lines.append(
                f"Durations: Grade 1={features_dict['grade_1_time_sec']:.0f}s, Grade 2={features_dict['grade_2_time_sec']:.0f}s, Grade 3={features_dict['grade_3_time_sec']:.0f}s."
            )

    # Return structured result adhering to contract
    return {
        "status": "ml_estimate",
        "score": score,
        "label": label,
        "features": {
            "valid_data_coverage": round(coverage, 3),
            "total_readings": total_readings,
            "valid_readings_count": valid_readings_count,
            "biological_type": bio_type,
            "grade_1_time_sec": features_dict["grade_1_time_sec"],
            "grade_2_time_sec": features_dict["grade_2_time_sec"],
            "grade_3_time_sec": features_dict["grade_3_time_sec"],
            "total_excursion_time_sec": total_exc_sec,
            "longest_excursion_sec": features_dict["longest_excursion_sec"],
            "max_grade_reached": max_grade,
            "crossing_count": crossing_count,
            "heat_grade_1_time_sec": features_dict["heat_grade_1_time_sec"],
            "heat_grade_2_time_sec": features_dict["heat_grade_2_time_sec"],
            "heat_grade_3_time_sec": features_dict["heat_grade_3_time_sec"],
            "cold_grade_1_time_sec": features_dict["cold_grade_1_time_sec"],
            "cold_grade_2_time_sec": features_dict["cold_grade_2_time_sec"],
            "cold_grade_3_time_sec": features_dict["cold_grade_3_time_sec"],
        },
        "shap_factors": shap_impacts,
        "explanation": explanation_lines,
        "method_version": ML_METHOD_VERSION,
        "disclaimer": ML_DISCLAIMER,
    }
