import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models.database import init_db

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

client = TestClient(app)

def test_profiles_seeded():
    response = client.get("/api/profiles")
    assert response.status_code == 200
    profiles = response.json()
    assert len(profiles) >= 3
    # Check that profiles are marked illustrative
    assert all(p["profile_kind"] == "illustrative" for p in profiles)
    profile_ids = [p["id"] for p in profiles]
    assert "demo-profile-standard-mab" in profile_ids

def test_shipment_crud_lifecycle():
    # 1. Create a shipment
    create_payload = {
        "profile_id": "demo-profile-standard-mab",
        "vial_count": 9,
        "sensor_count": 4,
        "scenario": "normal",
        "destination_label": "Judge Demo Testing Center",
    }
    create_res = client.post("/api/shipments", json=create_payload)
    assert create_res.status_code == 201
    shipment = create_res.json()
    shipment_id = shipment["id"]
    assert shipment["status"] == "created"
    assert shipment["vial_count"] == 9
    assert len(shipment["sensors"]) == 4

    # 2. Retrieve the shipment
    get_res = client.get(f"/api/shipments/{shipment_id}")
    assert get_res.status_code == 200
    retrieved = get_res.json()
    assert retrieved["id"] == shipment_id
    assert retrieved["profile"]["id"] == "demo-profile-standard-mab"

    # 3. List shipments
    list_res = client.get("/api/shipments")
    assert list_res.status_code == 200
    shipments = list_res.json()
    assert any(s["id"] == shipment_id for s in shipments)

    # 4. Update scenario
    scen_res = client.post(
        f"/api/shipments/{shipment_id}/scenario",
        json={"scenario": "gradual_warming"},
    )
    assert scen_res.status_code == 200
    assert scen_res.json()["scenario"] == "gradual_warming"

def test_invalid_shipment_vial_count():
    invalid_payload = {
        "profile_id": "demo-profile-standard-mab",
        "vial_count": 15,  # must be between 1 and 9
        "sensor_count": 2,
    }
    res = client.post("/api/shipments", json=invalid_payload)
    assert res.status_code == 422
