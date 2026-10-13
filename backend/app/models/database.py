import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from contextlib import contextmanager
from typing import Generator
from backend.app.config import DATABASE_PATH

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS product_profiles (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT,
    lower_limit_c REAL NOT NULL,
    upper_limit_c REAL NOT NULL,
    profile_kind TEXT NOT NULL,
    source_name TEXT,
    source_version TEXT,
    source_date TEXT,
    notes TEXT,
    demo_model_version TEXT,
    demo_parameters_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CHECK (lower_limit_c < upper_limit_c)
);

CREATE TABLE IF NOT EXISTS shipments (
    id TEXT PRIMARY KEY,
    profile_id TEXT NOT NULL REFERENCES product_profiles(id),
    status TEXT NOT NULL,
    vial_count INTEGER NOT NULL CHECK (vial_count >= 1 AND vial_count <= 9),
    sensor_count INTEGER NOT NULL CHECK (sensor_count > 0),
    destination_label TEXT,
    scenario TEXT NOT NULL,
    started_at TEXT,
    ended_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    operator_review_status TEXT,
    operator_review_note TEXT
);

CREATE TABLE IF NOT EXISTS sensors (
    id TEXT PRIMARY KEY,
    shipment_id TEXT NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
    label TEXT NOT NULL,
    position_x REAL NOT NULL,
    position_y REAL NOT NULL,
    position_z REAL NOT NULL,
    health_status TEXT NOT NULL,
    last_valid_temperature_c REAL,
    last_reading_at TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shipment_id TEXT NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
    sensor_id TEXT NOT NULL REFERENCES sensors(id) ON DELETE CASCADE,
    timestamp TEXT NOT NULL,
    temperature_c REAL,
    quality_status TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'simulated',
    scenario TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_readings_shipment_time ON readings(shipment_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_readings_sensor_time ON readings(sensor_id, timestamp);

CREATE TABLE IF NOT EXISTS excursion_events (
    id TEXT PRIMARY KEY,
    shipment_id TEXT NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
    sensor_id TEXT NOT NULL REFERENCES sensors(id) ON DELETE CASCADE,
    direction TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TEXT NOT NULL,
    last_breach_at TEXT NOT NULL,
    ended_at TEXT,
    duration_seconds REAL,
    peak_temperature_c REAL,
    minimum_temperature_c REAL,
    crossing_count INTEGER NOT NULL DEFAULT 1,
    max_rate_c_per_minute REAL,
    exposure_degree_minutes REAL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_excursions_shipment ON excursion_events(shipment_id);

CREATE TABLE IF NOT EXISTS alerts (
    id TEXT PRIMARY KEY,
    shipment_id TEXT NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
    sensor_id TEXT REFERENCES sensors(id) ON DELETE SET NULL,
    excursion_event_id TEXT REFERENCES excursion_events(id) ON DELETE SET NULL,
    type TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    acknowledged_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_alerts_shipment ON alerts(shipment_id);

CREATE TABLE IF NOT EXISTS assessments (
    id TEXT PRIMARY KEY,
    shipment_id TEXT NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
    review_status TEXT NOT NULL,
    review_note TEXT,
    reviewer_label TEXT,
    created_at TEXT NOT NULL,
    method_version TEXT,
    demo_score REAL,
    demo_label TEXT,
    features_json TEXT,
    explanation_json TEXT,
    disclaimer TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_assessments_shipment ON assessments(shipment_id);

CREATE TABLE IF NOT EXISTS nfc_transfers (
    id TEXT PRIMARY KEY,
    shipment_id TEXT NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    records_transferred INTEGER NOT NULL DEFAULT 0,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    message TEXT
);

CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shipment_id TEXT REFERENCES shipments(id) ON DELETE SET NULL,
    event_type TEXT NOT NULL,
    actor_label TEXT NOT NULL DEFAULT 'demo-user',
    timestamp TEXT NOT NULL,
    details_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_audit_shipment ON audit_events(shipment_id);
"""

SEED_PROFILES = [
    {
        "id": "demo-profile-standard-mab",
        "name": "Illustrative Demo: Monoclonal Antibody Solution (2°C to 8°C)",
        "category": "Standard Refrigerated Biologic",
        "lower_limit_c": 2.0,
        "upper_limit_c": 8.0,
        "profile_kind": "illustrative",
        "source_name": "Illustrative Demo Benchmark Specification",
        "source_version": "v1.0-demo",
        "source_date": "2026-10-01",
        "notes": "Thermal limits for standard cold-chain biologics.",
        "demo_model_version": "demo-v1",
        "demo_parameters_json": json.dumps({
            "baseline_temp_c": 5.0,
            "tolerance_degree_minutes": 15.0,
            "decay_rate_per_deg_min": 0.8,
            "noise_std": 0.2,
        }),
    },
    {
        "id": "demo-profile-ultracold-mrna",
        "name": "Illustrative Demo: mRNA Vaccine Formulation (-80°C to -60°C)",
        "category": "Ultra-Cold Storage",
        "lower_limit_c": -80.0,
        "upper_limit_c": -60.0,
        "profile_kind": "illustrative",
        "source_name": "Illustrative Demo Benchmark Specification",
        "source_version": "v1.0-demo",
        "source_date": "2026-10-01",
        "notes": "Ultra-cold thermal limits (dry ice packaging).",
        "demo_model_version": "demo-v1",
        "demo_parameters_json": json.dumps({
            "baseline_temp_c": -70.0,
            "tolerance_degree_minutes": 10.0,
            "decay_rate_per_deg_min": 1.2,
            "noise_std": 0.5,
        }),
    },
    {
        "id": "demo-profile-cryo-cellular",
        "name": "Illustrative Demo: Cryopreserved Cell Therapy (-150°C to -120°C)",
        "category": "Cryogenic Nitrogen Vapor",
        "lower_limit_c": -150.0,
        "upper_limit_c": -120.0,
        "profile_kind": "illustrative",
        "source_name": "Illustrative Demo Benchmark Specification",
        "source_version": "v1.0-demo",
        "source_date": "2026-10-01",
        "notes": "Cryogenic nitrogen vapor storage limits.",
        "demo_model_version": "demo-v1",
        "demo_parameters_json": json.dumps({
            "baseline_temp_c": -135.0,
            "tolerance_degree_minutes": 8.0,
            "decay_rate_per_deg_min": 1.5,
            "noise_std": 0.8,
        }),
    },
]

def get_db_path() -> Path:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    return DATABASE_PATH

@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(str(get_db_path()), timeout=20.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db() -> None:
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.executescript(SCHEMA_SQL)
        for profile in SEED_PROFILES:
            conn.execute(
                """
                INSERT OR IGNORE INTO product_profiles (
                    id, name, category, lower_limit_c, upper_limit_c,
                    profile_kind, source_name, source_version, source_date,
                    notes, demo_model_version, demo_parameters_json,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    profile["id"],
                    profile["name"],
                    profile["category"],
                    profile["lower_limit_c"],
                    profile["upper_limit_c"],
                    profile["profile_kind"],
                    profile["source_name"],
                    profile["source_version"],
                    profile["source_date"],
                    profile["notes"],
                    profile["demo_model_version"],
                    profile["demo_parameters_json"],
                    now_iso,
                    now_iso,
                ),
            )
