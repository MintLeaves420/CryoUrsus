import pytest
from datetime import datetime, timezone
from backend.app.models.database import init_db
from backend.app.services.sensor_validation import validate_sensor_reading
from backend.app.services.excursion_engine import process_reading_for_excursions
from backend.app.services.shipment_service import create_shipment, get_shipment_by_id
from backend.app.schemas.shipment import ShipmentCreateRequest
from backend.app.services.alert_service import list_alerts

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

def test_sensor_validation_stuck_and_implausible():
    # 1. Normal reading
    res = validate_sensor_reading(5.0, [4.8, 5.1, 4.9])
    assert res.quality_status == "valid"
    assert res.is_valid_for_excursion is True

    # 2. Stuck reading (identical for >= 5 readings)
    frozen_history = [5.0, 5.0, 5.0, 5.0]
    res_stuck = validate_sensor_reading(5.0, frozen_history)
    assert res_stuck.quality_status == "stuck"
    assert res_stuck.is_valid_for_excursion is False
    assert "frozen" in res_stuck.diagnostic_reason.lower()

    # 3. Disconnected reading
    res_disc = validate_sensor_reading(None, [5.0], is_explicitly_disconnected=True)
    assert res_disc.quality_status == "disconnected"
    assert res_disc.is_valid_for_excursion is False

    # 4. Implausible reading (extreme value)
    res_impl = validate_sensor_reading(120.0, [5.0])
    assert res_impl.quality_status == "implausible"
    assert res_impl.is_valid_for_excursion is False

def test_excursion_engine_upper_and_lower_breaches():
    shp = create_shipment(ShipmentCreateRequest(
        profile_id="demo-profile-standard-mab",
        vial_count=5,
        sensor_count=2,
    ))
    sensor_id = shp.sensors[0].id
    lower_limit = 2.0
    upper_limit = 8.0

    now_iso = datetime.now(timezone.utc).isoformat()

    # Reading within limits: no excursion
    evt1 = process_reading_for_excursions(shp.id, sensor_id, 5.0, lower_limit, upper_limit, now_iso)
    assert evt1 is None

    # Reading above upper limit (8.0): triggers upper excursion
    evt2 = process_reading_for_excursions(shp.id, sensor_id, 10.5, lower_limit, upper_limit, now_iso)
    assert evt2 is not None
    assert evt2["event"] == "excursion_started"
    assert evt2["direction"] == "upper"

    # Verify persisted alert
    alerts = list_alerts(shipment_id=shp.id)
    assert len(alerts) >= 1
    assert any(a.type == "upper_limit" and a.status == "active" for a in alerts)

    # Return to normal: should resolve excursion and alert
    evt3 = process_reading_for_excursions(shp.id, sensor_id, 4.0, lower_limit, upper_limit, now_iso)
    assert evt3 is not None
    assert evt3["event"] == "excursion_resolved"

    active_alerts = list_alerts(shipment_id=shp.id, status="active")
    assert len(active_alerts) == 0
