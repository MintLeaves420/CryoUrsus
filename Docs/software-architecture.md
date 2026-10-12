# CryoUrsus --- Software Architecture

## 1. Architecture summary

CryoUrsus is a local-first, single-backend web application for a
simulated cold-chain shipment. The React client presents the 3D
truck/package view and operational dashboards. FastAPI owns simulation
lifecycle, readings, excursion logic, alerts, demo-only viability
estimates, persistence, and report generation. SQLite stores the
authoritative records.

``` text
React + TypeScript + Vite
  ├── Truck / Package Simulator
  ├── Operator Dashboard
  ├── Owner Dashboard
  ├── Charts, tables, alert panels
  └── API service + WebSocket client
             │ HTTP + WebSocket
             ▼
FastAPI application
  ├── Shipment service
  ├── Simulation engine
  ├── Sensor validation
  ├── Excursion engine
  ├── Demo viability estimator
  ├── Explanation builder
  ├── Alert service
  ├── Simulated NFC transfer
  ├── Report service
  └── Audit event service
             │
             ▼
          SQLite
  ├── product_profiles
  ├── shipments
  ├── sensors
  ├── readings
  ├── excursion_events
  ├── alerts
  ├── assessments
  ├── nfc_transfers
  └── audit_events
```

## 2. Architectural principles

1.  **One source of truth:** backend state is authoritative.
2.  **Simulation-first:** all virtual readings and demo profiles are
    explicitly labelled.
3.  **Explainability:** every alert and demo estimate can be traced to
    recorded features and rules.
4.  **Modular domain logic:** simulation, excursion detection,
    prediction, alerts, and reporting are separate modules.
5.  **Simple local deployment:** no external service is required for the
    main demo.
6.  **Graceful degradation:** charts/tables remain useful if 3D
    rendering or WebSockets fail.
7.  **Human review:** the application informs a reviewer; it does not
    autonomously release or reject real product.

## 3. Technology choices

-   **Frontend:** React, TypeScript, Vite.
-   **3D:** Three.js, React Three Fiber; optionally Drei for camera
    controls and helpers.
-   **Charts:** Recharts.
-   **Backend:** Python, FastAPI, Pydantic.
-   **Live updates:** FastAPI WebSockets; polling fallback may be used.
-   **Database:** SQLite.
-   **PDF:** ReportLab or another explicitly selected Python PDF
    library.
-   **Tests:** pytest for backend; Vitest/React Testing Library for
    frontend if present.
-   **ML/demo estimator:** deterministic formula or small interpretable
    scikit-learn model only if it adds value. Do not add ML merely for
    appearance.

Check the repository before installing or replacing dependencies.

## 4. Frontend structure

Suggested structure:

``` text
frontend/
  src/
    app/
      App.tsx
      routes.tsx
    pages/
      TruckDashboard.tsx
      OperatorDashboard.tsx
      OwnerDashboard.tsx
      ShipmentDetail.tsx
    components/
      Package3D.tsx
      VialTray.tsx
      SensorMarker.tsx
      SimulationControls.tsx
      TemperatureChart.tsx
      ReadingsTable.tsx
      AlertBanner.tsx
      ShipmentStatusBadge.tsx
      ExplanationPanel.tsx
      ReportDownload.tsx
    services/
      api.ts
      websocket.ts
    hooks/
      useShipment.ts
      useLiveEvents.ts
    types/
      api.ts
      domain.ts
    utils/
      date.ts
      formatting.ts
```

The exact route approach may be selected based on the starter
repository. Avoid duplicating page state. Reuse a single shipment
store/hook or query layer.

### Frontend responsibilities

-   Render the current shipment and dashboard.
-   Submit user commands to the API.
-   Subscribe to backend events.
-   Display live readings, alert transitions, and sensor health.
-   Show 3D package and vial positions.
-   Offer clear connection/staleness status.
-   Never decide the authoritative excursion or shipment outcome
    independently.

## 5. Backend structure

Suggested structure:

``` text
backend/
  app/
    main.py
    config.py
    api/
      routes_shipments.py
      routes_profiles.py
      routes_readings.py
      routes_alerts.py
      routes_reports.py
      routes_nfc.py
      websocket.py
    schemas/
      shipment.py
      reading.py
      alert.py
      assessment.py
      profile.py
    models/
      database.py
      entities.py
    services/
      shipment_service.py
      simulation_service.py
      sensor_validation.py
      excursion_engine.py
      viability_estimator.py
      explanation_service.py
      alert_service.py
      nfc_service.py
      report_service.py
      audit_service.py
    repositories/
      shipments.py
      readings.py
      alerts.py
      profiles.py
    tests/
```

This is a suggested layout, not a reason to move files unnecessarily if
a working repository already exists.

## 6. Main data flow

1.  User creates a shipment with a product profile, vial count, and
    sensor configuration.
2.  Backend persists the shipment and virtual sensor definitions.
3.  User starts the simulation.
4.  Simulation service generates a bounded set of timestamped readings
    per tick.
5.  Sensor validation classifies readings as valid, stale, stuck,
    disconnected, or implausible.
6.  Valid readings are passed to the excursion engine.
7.  The excursion engine updates active event state and computes
    features.
8.  Alert service persists newly created or changed alerts.
9.  Demo viability estimator evaluates the available features if data
    quality and profile requirements are met.
10. Explanation service describes the actual rules/features behind the
    result.
11. Readings, events, and alerts are committed to SQLite.
12. WebSocket messages notify connected clients after persistence.
13. Operator and Owner views update from the same event stream and
    persisted API state.
14. Report service builds a PDF from persisted data and includes the
    demo disclaimer.
15. Audit service records relevant user and system actions.

## 7. Simulation design

### Tick lifecycle

Each active shipment has at most one simulation task. On each tick: -
Read the shipment's configured scenario and profile. - Generate the next
temperature for each virtual sensor. - Apply the configured fault mode
if selected. - Validate readings and store the raw observation plus
quality state. - Run excursion detection only on valid observations. -
Update alerts and feature summaries. - Persist state, then broadcast an
event. - Stop when the shipment is ended or the task is cancelled.

Use an asyncio task registry or an equivalent lifecycle manager. Avoid
untracked background tasks and duplicate loops. The tick interval should
be configurable (for example, 1--2 seconds for presentation use).

### Scenarios

-   Normal: readings fluctuate slightly around a baseline within limits.
-   Gradual warming / cooling: readings trend toward and then across a
    limit.
-   Sudden spike / drop: one or more readings move quickly across a
    limit.
-   Repeated fluctuations: repeated crossings to demonstrate event
    transitions.
-   Stuck sensor: values remain unchanged for a configured number of
    samples.
-   Disconnected sensor: readings stop or health becomes disconnected.
-   Implausible reading: deliberately invalid/out-of-range sensor value
    is flagged as bad data, not treated as a trustworthy excursion.

Use a fixed random seed or scenario parameters when repeatability
matters.

## 8. Excursion logic

The excursion engine should be deterministic and independently tested.

-   A valid temperature below the lower limit or above the upper limit
    is a breach.
-   Equality with a limit is considered within range for the MVP.
-   Store breach start, latest breach time, end time when resolved,
    duration, maximum, minimum, and relevant
    rate-of-change/cumulative-exposure features.
-   Record entry and exit transitions.
-   Do not create a separate alert for every reading during the same
    active event.
-   If all sensors are invalid, disconnected, or stale, show
    "Insufficient trustworthy data" rather than "within limits."
-   Sensor-health events are not temperature excursions by themselves.

The implementation must document how readings from multiple sensors are
summarized. A conservative and simple MVP approach is to evaluate each
sensor independently and show the worst observed condition, without
hiding individual sensor history.

## 9. Demo viability and XAI

Keep the following separate: - **Excursion engine:** determines
rule-based temperature and data-quality events. - **Feature builder:**
creates metrics such as exposure duration, peak/minimum, number of
crossings, rate of change, and valid-data coverage. - **Demo viability
estimator:** returns a deterministic illustrative score/category, or
"Insufficient data." - **Explanation service:** converts the actual
inputs and decision path into a concise explanation. - **Human
assessment:** an operator's review status and note.

For the MVP, prefer a transparent illustrative formula with named
parameters over an unsupported model trained on fabricated data. If a
scikit-learn model is used, document its synthetic training data and
limitations. Do not imply model validation.

Suggested response shape:

``` json
{
  "status": "demo_estimate",
  "score": 82,
  "label": "Illustrative estimate",
  "features": {
    "valid_data_coverage": 0.98,
    "upper_breach_seconds": 12,
    "lower_breach_seconds": 0,
    "crossing_count": 1
  },
  "explanation": [
    "A brief upper-limit excursion was recorded.",
    "The score is generated by the configured demonstration method."
  ],
  "method_version": "demo-v1",
  "disclaimer": "Simulation estimate only; not validated for product release or clinical use."
}
```

The score above is only an example schema, not a prescribed model
output.

## 10. Real-time events

Use WebSockets for live reading, alert, shipment-status, and
sensor-health updates.

Example envelope:

``` json
{
  "type": "reading.created",
  "version": 1,
  "shipment_id": "shp_example",
  "timestamp": "2026-10-13T12:00:00Z",
  "data": {}
}
```

Possible event types: - `shipment.status_changed` - `reading.created` -
`sensor.health_changed` - `excursion.started` - `excursion.updated` -
`excursion.ended` - `alert.created` - `alert.updated` -
`assessment.updated` - `nfc.transfer_updated`

Persist state before broadcasting. Client reconnect should fetch a fresh
snapshot through REST. If WebSockets are disconnected, show that state
may be stale and use polling if implemented.

## 11. Security and privacy

-   The demo should not require real patient or personal data.
-   Use fictional shipment IDs and destinations.
-   Restrict CORS to known local development origins.
-   Validate and bound input values.
-   Do not expose filesystem paths or stack traces in production-style
    API responses.
-   Do not commit `.env` or credentials.
-   If authentication is not implemented, state that the role switch is
    demonstrative and not a security boundary.

## 12. Deployment

Primary target: local laptop demo, with frontend and backend running
separately.

-   Frontend: Vite development server.
-   Backend: Uvicorn running FastAPI.
-   Database: SQLite file in a documented application data location.
-   Provide `.env.example`, `.gitignore`, startup commands, and seeded
    demo profiles.
-   Keep the main demo usable without third-party APIs or internet
    access after dependencies are installed.

## 13. Architecture decision records

### ADR-001: Single FastAPI backend

**Decision:** Use one FastAPI application for the MVP.\
**Reason:** Reduces operational complexity and keeps state consistent
across dashboards.\
**Trade-off:** Not designed for large-scale production traffic.

### ADR-002: SQLite persistence

**Decision:** SQLite is the MVP database.\
**Reason:** Easy to run locally and sufficient for a single-demo
workload.\
**Trade-off:** Not intended for high-concurrency production deployment.

### ADR-003: Simulated sensor/NFC input

**Decision:** Virtualize sensor readings and NFC handoff.\
**Reason:** The hackathon accepts simulation and does not require
hardware.\
**Trade-off:** Demonstrates workflow and reasoning, not physical-device
accuracy.

### ADR-004: Transparent demo viability method

**Decision:** Use a clearly labelled deterministic illustrative
estimator unless verified stability data and a validated method are
available.\
**Reason:** Avoids false claims about actual biologic viability.\
**Trade-off:** The score is pedagogical, not a real-world potency
prediction.
