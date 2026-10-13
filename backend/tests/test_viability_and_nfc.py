import pytest
from backend.app.models.database import init_db
from backend.app.services.viability_estimator import calculate_demo_viability
from backend.app.services.nfc_service import trigger_simulated_nfc_transfer, get_nfc_transfer_by_id
from backend.app.services.shipment_service import create_shipment
from backend.app.schemas.shipment import ShipmentCreateRequest
from backend.app.services.report_service import generate_shipment_pdf

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

def test_viability_estimator_ml():
    # 1. Normal shipment with no excursions
    res1 = calculate_demo_viability(valid_readings_count=100, total_readings=100, excursion_events=[])
    assert res1["status"] == "ml_estimate"
    assert res1["score"] >= 99.0
    assert "Optimal" in res1["label"]
    assert "RandomForest" in res1["method_version"]

    # 2. Incomplete or low coverage (< 50%) -> Insufficient trustworthy data
    res_low = calculate_demo_viability(valid_readings_count=30, total_readings=100, excursion_events=[])
    assert res_low["status"] == "insufficient_data"
    assert res_low["score"] is None
    assert "Insufficient" in res_low["label"]

    # 3. Determinism: identical excursion inputs yield identical ML prediction & SHAP factors
    exc_sample = [{"direction": "upper", "duration_seconds": 60.0, "peak_temperature_c": 12.0}]
    res_a = calculate_demo_viability(valid_readings_count=90, total_readings=100, excursion_events=exc_sample)
    res_b = calculate_demo_viability(valid_readings_count=90, total_readings=100, excursion_events=exc_sample)
    assert res_a["score"] == res_b["score"]
    assert res_a["score"] < 100.0
    assert "CryoUrsus" in res_a["disclaimer"]
    assert len(res_a["explanation"]) > 0

def test_temperature_grade_classification():
    from backend.app.services.excursion_engine import classify_temperature_grade
    # Monoclonal Antibody limits: 2.0 to 8.0 C
    # Within range -> Grade 0
    assert classify_temperature_grade(5.0, 2.0, 8.0) == ("normal", 0, 0.0)
    # Heat Grade 1: 8.0 to 10.0 C
    assert classify_temperature_grade(9.5, 2.0, 8.0) == ("heat", 1, 1.5)
    # Heat Grade 2: 10.0 to 13.0 C
    assert classify_temperature_grade(11.5, 2.0, 8.0) == ("heat", 2, 3.5)
    # Heat Grade 3: > 13.0 C
    assert classify_temperature_grade(15.0, 2.0, 8.0) == ("heat", 3, 7.0)

    # Cold Grade 1: 0.0 to 2.0 C
    assert classify_temperature_grade(1.0, 2.0, 8.0) == ("cold", 1, 1.0)
    # Cold Grade 2: -3.0 to 0.0 C
    assert classify_temperature_grade(-1.0, 2.0, 8.0) == ("cold", 2, 3.0)
    # Cold Grade 3: < -3.0 C
    assert classify_temperature_grade(-5.0, 2.0, 8.0) == ("cold", 3, 7.0)

def test_ml_model_and_shap_explainability():
    from backend.app.services.viability_estimator import get_ml_model
    pipeline, explainer = get_ml_model()
    assert pipeline is not None
    assert explainer is not None

    # Test prediction with severe excursion
    exc = [
        {"direction": "upper", "duration_seconds": 120.0, "peak_temperature_c": 16.0},
        {"direction": "lower", "duration_seconds": 45.0, "minimum_temperature_c": -2.0},
    ]
    res = calculate_demo_viability(
        valid_readings_count=100,
        total_readings=100,
        excursion_events=exc,
        lower_limit_c=2.0,
        upper_limit_c=8.0,
    )
    assert res["status"] == "ml_estimate"
    assert res["score"] < 95.0
    assert "shap_factors" in res
    assert any("SHAP Impact:" in line for line in res["explanation"])

def test_nfc_and_pdf_generation():
    shp = create_shipment(ShipmentCreateRequest(
        profile_id="demo-profile-standard-mab",
        vial_count=9,
        sensor_count=3,
    ))

    # NFC Transfer
    nfc_res = trigger_simulated_nfc_transfer(shp.id)
    assert nfc_res.status == "success"
    assert nfc_res.shipment_id == shp.id

    fetched_nfc = get_nfc_transfer_by_id(nfc_res.id)
    assert fetched_nfc is not None
    assert fetched_nfc.id == nfc_res.id

    # PDF Generation
    pdf_buffer = generate_shipment_pdf(shp.id)
    pdf_bytes = pdf_buffer.getvalue()
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")
