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

def test_viability_estimator_determinism():
    # 1. Normal shipment with no excursions
    res1 = calculate_demo_viability(valid_readings_count=100, total_readings=100, excursion_events=[])
    assert res1["status"] == "demo_estimate"
    assert res1["score"] == 100.0
    assert "Optimal" in res1["label"]

    # 2. Incomplete or low coverage (< 50%) -> Insufficient trustworthy data
    res_low = calculate_demo_viability(valid_readings_count=30, total_readings=100, excursion_events=[])
    assert res_low["status"] == "insufficient_data"
    assert res_low["score"] is None
    assert "Insufficient" in res_low["label"]

    # 3. Determinism: identical inputs yield identical score
    exc_sample = [{"direction": "upper", "duration_seconds": 60, "exposure_degree_minutes": 5.0}]
    res_a = calculate_demo_viability(valid_readings_count=90, total_readings=100, excursion_events=exc_sample)
    res_b = calculate_demo_viability(valid_readings_count=90, total_readings=100, excursion_events=exc_sample)
    assert res_a["score"] == res_b["score"]
    assert res_a["score"] < 100.0
    assert "CryoUrsus" in res_a["disclaimer"]

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
