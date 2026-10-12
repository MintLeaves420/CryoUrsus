# CryoUrsus --- Data Model

This document defines the logical SQLite data model. Implement the
smallest useful schema and add migrations or safe schema initialization.
Use UTC ISO 8601 timestamps in API representations.

## 1. Entities and relationships

``` text
ProductProfile 1 ─── * Shipment
Shipment       1 ─── * Sensor
Shipment       1 ─── * Reading
Sensor         1 ─── * Reading
Shipment       1 ─── * ExcursionEvent
Shipment       1 ─── * Alert
Shipment       1 ─── * Assessment
Shipment       1 ─── * NFCTransfer
Shipment       1 ─── * AuditEvent
```

## 2. Tables

### `product_profiles`

-   `id` TEXT PRIMARY KEY
-   `name` TEXT NOT NULL
-   `category` TEXT
-   `lower_limit_c` REAL NOT NULL
-   `upper_limit_c` REAL NOT NULL
-   `profile_kind` TEXT NOT NULL --- `illustrative` or `verified_source`
-   `source_name` TEXT
-   `source_version` TEXT
-   `source_date` TEXT
-   `notes` TEXT
-   `demo_model_version` TEXT
-   `demo_parameters_json` TEXT
-   `created_at` TEXT NOT NULL
-   `updated_at` TEXT NOT NULL

Validation: `lower_limit_c < upper_limit_c`. Seeded sample profiles must
be labelled illustrative unless verified product-specific documentation
is actually supplied.

### `shipments`

-   `id` TEXT PRIMARY KEY
-   `profile_id` TEXT NOT NULL REFERENCES `product_profiles(id)`
-   `status` TEXT NOT NULL --- `created`, `running`, `paused`,
    `completed`, `review_required`
-   `vial_count` INTEGER NOT NULL CHECK between 1 and 9
-   `sensor_count` INTEGER NOT NULL CHECK greater than 0
-   `destination_label` TEXT NULL --- fictional/demo only
-   `scenario` TEXT NOT NULL
-   `started_at` TEXT NULL
-   `ended_at` TEXT NULL
-   `created_at` TEXT NOT NULL
-   `updated_at` TEXT NOT NULL
-   `operator_review_status` TEXT NULL
-   `operator_review_note` TEXT NULL

### `sensors`

-   `id` TEXT PRIMARY KEY
-   `shipment_id` TEXT NOT NULL REFERENCES `shipments(id)`
-   `label` TEXT NOT NULL
-   `position_x` REAL NOT NULL
-   `position_y` REAL NOT NULL
-   `position_z` REAL NOT NULL
-   `health_status` TEXT NOT NULL --- `healthy`, `stuck`,
    `disconnected`, `implausible`, `stale`
-   `last_valid_temperature_c` REAL NULL
-   `last_reading_at` TEXT NULL
-   `created_at` TEXT NOT NULL

Sensor positions are for the 3D scene. They are independent of the vial
layout.

### `readings`

-   `id` INTEGER PRIMARY KEY AUTOINCREMENT
-   `shipment_id` TEXT NOT NULL REFERENCES `shipments(id)`
-   `sensor_id` TEXT NOT NULL REFERENCES `sensors(id)`
-   `timestamp` TEXT NOT NULL
-   `temperature_c` REAL NULL
-   `quality_status` TEXT NOT NULL --- `valid`, `stuck`, `disconnected`,
    `implausible`, `stale`
-   `source` TEXT NOT NULL DEFAULT `simulated`
-   `scenario` TEXT
-   `created_at` TEXT NOT NULL

Index by `(shipment_id, timestamp)` and `(sensor_id, timestamp)`.
Invalid sensor observations may have a null temperature if no value was
received; do not fabricate a valid temperature for a disconnected
sensor.

### `excursion_events`

-   `id` TEXT PRIMARY KEY
-   `shipment_id` TEXT NOT NULL REFERENCES `shipments(id)`
-   `sensor_id` TEXT NOT NULL REFERENCES `sensors(id)`
-   `direction` TEXT NOT NULL --- `upper`, `lower`
-   `status` TEXT NOT NULL --- `active`, `resolved`
-   `started_at` TEXT NOT NULL
-   `last_breach_at` TEXT NOT NULL
-   `ended_at` TEXT NULL
-   `duration_seconds` REAL NULL
-   `peak_temperature_c` REAL NULL
-   `minimum_temperature_c` REAL NULL
-   `crossing_count` INTEGER NOT NULL DEFAULT 1
-   `max_rate_c_per_minute` REAL NULL
-   `exposure_degree_minutes` REAL NULL
-   `created_at` TEXT NOT NULL
-   `updated_at` TEXT NOT NULL

Use one event per continuous breach per sensor/direction; record
transitions instead of one event per sample.

### `alerts`

-   `id` TEXT PRIMARY KEY
-   `shipment_id` TEXT NOT NULL REFERENCES `shipments(id)`
-   `sensor_id` TEXT NULL REFERENCES `sensors(id)`
-   `excursion_event_id` TEXT NULL REFERENCES `excursion_events(id)`
-   `type` TEXT NOT NULL --- `upper_limit`, `lower_limit`,
    `sensor_fault`, `data_quality`
-   `severity` TEXT NOT NULL --- `info`, `warning`, `critical`
-   `status` TEXT NOT NULL --- `active`, `acknowledged`, `resolved`
-   `title` TEXT NOT NULL
-   `message` TEXT NOT NULL
-   `created_at` TEXT NOT NULL
-   `updated_at` TEXT NOT NULL
-   `acknowledged_at` TEXT NULL

### `assessments`

-   `id` TEXT PRIMARY KEY
-   `shipment_id` TEXT NOT NULL REFERENCES `shipments(id)`
-   `review_status` TEXT NOT NULL --- e.g. `pending`, `reviewed`,
    `requires_follow_up`
-   `review_note` TEXT
-   `reviewer_label` TEXT
-   `created_at` TEXT NOT NULL
-   `method_version` TEXT
-   `demo_score` REAL NULL
-   `demo_label` TEXT
-   `features_json` TEXT
-   `explanation_json` TEXT
-   `disclaimer` TEXT NOT NULL

Do not store the demo score as actual measured potency.

### `nfc_transfers`

-   `id` TEXT PRIMARY KEY
-   `shipment_id` TEXT NOT NULL REFERENCES `shipments(id)`
-   `status` TEXT NOT NULL --- `started`, `success`, `failed`
-   `records_transferred` INTEGER NOT NULL DEFAULT 0
-   `started_at` TEXT NOT NULL
-   `completed_at` TEXT NULL
-   `message` TEXT

### `audit_events`

-   `id` INTEGER PRIMARY KEY AUTOINCREMENT
-   `shipment_id` TEXT NULL REFERENCES `shipments(id)`
-   `event_type` TEXT NOT NULL
-   `actor_label` TEXT NOT NULL DEFAULT `demo-user`
-   `timestamp` TEXT NOT NULL
-   `details_json` TEXT

Audit event rows should be append-only for normal application behavior.

## 3. Status semantics

-   `running`: simulation task is actively generating readings.
-   `paused`: shipment remains open but readings are temporarily
    stopped.
-   `completed`: simulation has ended.
-   `review_required`: optional computed/operational state indicating a
    human review is needed; do not use it to imply regulatory
    disposition.
-   `operator_review_status`: a separate human assessment field.

Do not collapse sensor-health status, excursion status, demo estimate,
and operator review into one ambiguous status.

## 4. Example seed profiles

Seed 2--3 illustrative profiles for demonstration. Example names may be
fictional and must be visibly labelled `Illustrative demo profile`.
Choose values deliberately for showing upper/lower breaches, not as
claimed real product specifications. Keep all parameters in seed/config
files, not scattered across business logic.

## 5. Retention and volume

The demo can retain all readings for the local presentation. Keep the
simulation tick interval and sensor count bounded. If a cleanup/reset
command is provided, make it explicit and require deliberate invocation.
