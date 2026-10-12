# CryoUrsus --- Product Requirements Document

**Document status:** Build specification for hackathon demo\
**Product type:** Interactive web-based cold-chain simulation and
decision-support demo\
**Primary audience:** Hackathon judges, shipment operators, cold-chain
owners\
**Implementation principle:** Demonstrate the workflow convincingly
without claiming that simulated outputs are validated medical or
product-safety decisions.

## 1. Product vision

CryoUrsus is an interactive cold-chain monitoring and explainable
decision-support demo for temperature-sensitive biologics. It simulates
a shipment, visualizes package temperatures, detects excursions and
sensor faults, estimates a demonstration-only remaining-viability score,
explains its reasoning, and makes the same shipment record available to
operators and owners.

The hackathon scope is a software simulation. No physical sensors,
ESP32, NFC reader, or actual biologic samples are required.

## 2. Problem statement

Temperature-sensitive biologics can experience conditions outside their
permitted storage range during transport. A useful monitoring workflow
needs to preserve timestamped evidence, identify excursions and sensor
faults, communicate alerts, and present a traceable assessment that a
human can review.

## 3. Goals

1.  Deliver a live, interactive website suitable for a judge-facing
    demonstration.
2.  Provide three coordinated views: Truck / Package Simulator, Operator
    Dashboard, and Owner Dashboard.
3.  Simulate multiple temperature sensors and a package containing up to
    nine vial positions.
4.  Detect upper- and lower-limit breaches, excursion duration, thermal
    shocks, repeated excursions, and sensor faults.
5.  Show a clearly labelled demonstration-only remaining-viability
    estimate with an understandable explanation.
6.  Persist shipments, readings, alerts, assessments, and report
    metadata in SQLite through a FastAPI backend.
7.  Provide simulated NFC transfer, downloadable reports, and an
    auditable event history.
8.  Make normal, excursion, and sensor-fault scenarios reproducible for
    the presentation.

## 4. Non-goals

-   Real hardware integration or real NFC communication.
-   Medical advice, regulatory certification, or autonomous
    release/rejection of actual biologics.
-   Claiming validated potency, shelf-life, or remaining viability.
-   Live scraping of pharmacopoeias, manufacturer portals, or regulatory
    sources.
-   Real SMS, WhatsApp, or email delivery in the MVP.
-   Multi-tenant production security, cloud deployment hardening, or
    production-scale telemetry.
-   Humidity or accelerometer sensing.
-   Complex, opaque ML models that cannot be explained during the demo.

## 5. Users and permissions

### Operator

-   Starts or reviews a simulated shipment.
-   Reviews readings, excursions, alerts, model output, and explanation.
-   Records an assessment and downloads a report.

### Owner / Logistics manager

-   Views all demo shipments and their statuses.
-   Sees current alert state, latest readings, operator assessments, and
    shipment history.
-   Opens shipment details and downloads reports.

### Presenter / Demo user

-   Operates the truck simulation controls and chooses a scenario.
-   Can switch among dashboard views without losing the active shipment.

For the hackathon MVP, role selection may be a UI mode rather than a
real authentication system. Do not represent this as secure access
control.

## 6. Core user journeys

### Journey A --- Normal shipment

1.  Select a product profile.
2.  Configure shipment parameters and vial count.
3.  Start simulation.
4.  Observe sensor readings remaining within the configured range.
5.  Pause or end the simulation.
6.  Review a normal status, explanation, and generated report.

### Journey B --- Temperature excursion

1.  Start a shipment.
2.  Trigger gradual warming/cooling or a sudden spike/drop.
3.  Watch readings and chart update in real time.
4.  See an upper- or lower-limit alert appear and persist.
5.  Review excursion duration, peak/minimum, cumulative exposure
    features, and explanation.
6.  Review the demonstration viability score and report.

### Journey C --- Sensor malfunction

1.  Start a shipment.
2.  Trigger a stuck, implausible, or disconnected sensor.
3.  See a sensor-health warning distinct from a temperature excursion.
4.  Confirm that the system does not silently treat bad data as
    trustworthy.
5.  Review the event in the operator and owner views and report.

### Journey D --- Simulated NFC handoff

1.  Select "Read NFC".
2.  Show a connection / transfer progress state.
3.  Send the selected shipment's locally simulated package history to
    the backend.
4.  Confirm transfer success or a clear error.
5.  Persist a transfer event in the audit history.

## 7. Functional requirements

### FR-1: Navigation and shared state

-   The app must provide Truck, Operator, and Owner views.
-   All views must reference the same shipment IDs and backend records.
-   Switching views must not create duplicate shipments or lose an
    active simulation.
-   Display a clear demo/simulation indicator.

### FR-2: Shipment configuration

-   Allow selection of a configured product profile.
-   Allow a vial count from 1 to 9.
-   Generate a unique shipment ID and show start time in the browser's
    local timezone.
-   Show product name, configured storage range, shipment status, and
    selected sensor count.
-   Profile fields must include units and a source/version note where
    applicable.

### FR-3: Truck / package visualization

-   Render a rotatable and zoomable 3D package/truck scene.
-   Render a 3×3 vial layout, with unused positions visually empty when
    vial count is below nine.
-   Show sensor markers separately from vial positions; sensors are not
    implicitly one-per-vial.
-   Selecting a sensor displays its ID, current temperature, last
    update, and health.
-   Include a readable 2D chart and latest-readings table; 3D must not
    be the only way to inspect data.

### FR-4: Simulation controls

-   Start, pause, resume, and end a simulation.
-   Offer reproducible scenarios: Normal, Gradual Warming, Gradual
    Cooling, Sudden Spike, Sudden Drop, Repeated Fluctuations, Sensor
    Stuck, Sensor Disconnected, and Implausible Reading.
-   Support a controlled manual temperature override for demonstration.
-   Show simulation time and event counters.
-   Ensure paused simulations do not generate new readings.
-   Ensure ending a simulation finalizes the shipment and stops its
    timer/task.

### FR-5: Readings and excursion engine

-   Generate timestamped readings for each active virtual sensor.
-   Record sensor ID, shipment ID, temperature, unit, health state, and
    source (`simulated`).
-   Compare readings with the selected profile's configured upper and
    lower limits.
-   Detect and record upper-limit and lower-limit breaches.
-   Track start time, end time, duration, peak/minimum, breach count,
    rate of change, and cumulative exposure features where available.
-   Apply sensor-quality checks before relying on a reading.
-   Separate sensor-fault events from product-temperature excursion
    events.
-   Use deterministic scenario seeds or repeatable scenario settings
    where practical.

### FR-6: Alerts

-   Create an alert when a valid reading crosses above the configured
    upper limit or below the configured lower limit.
-   Create a sensor-health alert for a disconnected, stuck, or
    implausible sensor.
-   Avoid generating a new duplicate alert for every sample during one
    continuous breach. Store event transitions and update the ongoing
    event.
-   Display alert severity, reason, affected sensor(s), event time, and
    acknowledgement state.
-   Update the Truck, Operator, and Owner views from the same backend
    state.
-   Persist alert events and include them in reports.
-   In-app alerts are required; external notifications are out of scope.

### FR-7: Remaining-viability demonstration

-   Calculate a demo-only viability indicator from documented,
    deterministic features or a simple transparent model.
-   Display the inputs/features used and a plain-language explanation of
    the result.
-   Display the method/version and a clear warning: "Simulation estimate
    only --- not validated for product release or clinical use."
-   Never present a simulated score as measured potency, a real
    shelf-life prediction, or an approved disposition.
-   If no valid readings exist, the sensor data are unreliable, or the
    profile is incomplete, return "Insufficient data" rather than a
    confident score.
-   Keep the excursion engine, demo predictor, and explanation layer as
    separate modules.

### FR-8: Operator dashboard

-   List shipments and show product, status, start/end time, last
    reading, alerts, and assessment.
-   Provide shipment detail with chart, readings, event timeline,
    excursion metrics, sensor health, demo viability indicator, and
    explanation.
-   Permit an operator to record a review status and note.
-   Distinguish computed technical status from human review status.

### FR-9: Owner dashboard

-   List all shipments with searchable/filterable status.
-   Surface active alerts and unresolved sensor faults.
-   Show destination as optional demo metadata, not a real inferred
    location.
-   Open shipment details and report download.
-   Show last update and data freshness.

### FR-10: Simulated NFC transfer

-   Simulate a scan and transfer interaction with clear UI states: idle,
    scanning, transferring, success, failure.
-   Transfer or re-read persisted shipment data via the backend; do not
    pretend the browser has accessed physical NFC hardware.
-   Record transfer time, shipment ID, record count, and result.

### FR-11: Reports

-   Generate a downloadable PDF report for a shipment.
-   Include shipment metadata, product profile/version, simulated
    readings summary, excursions, alerts, sensor faults, operator
    review, model version, explanation, and disclaimer.
-   Clearly label the report and all generated data as simulated.
-   Handle missing or empty data gracefully.

### FR-12: Audit history

-   Record key events: shipment created/started/paused/resumed/ended,
    scenario changes, sensor faults, excursions, alert acknowledgement,
    NFC simulation, operator assessment, and report generation.
-   Store timestamps in UTC in the backend and display them in the
    user's local timezone.
-   Do not silently rewrite past event records.

## 8. Product profile requirements

A profile should contain: - Stable profile ID and display name. - Demo
label and product category. - Lower and upper configured temperature
limits, with unit. - Optional excursion rules, only when deliberately
supplied for the demo. - Source label, source version/date, and notes. -
Demo stability parameters used by the illustrative predictor. - A flag
indicating whether the profile is illustrative or based on a verified
source.

Do not invent official limits or imply that one product's profile
applies to all biologics. Seed a small number of clearly illustrative
profiles for the demo. Any real product-specific rules must be checked
against the applicable manufacturer-approved product information and
stability documentation.

## 9. UX and visual direction

-   Premium, calm, technical, uncluttered interface.
-   Strong information hierarchy; reserve strong warning colors for
    meaningful alert states.
-   Always show units, timestamps, and sensor health.
-   Use labels and icons as well as color, for accessibility.
-   Responsive enough for a laptop presentation and a standard desktop
    browser.
-   Include empty, loading, paused, completed, and error states.
-   Provide a clear "Demo simulation --- not a validated cold-chain
    system" indicator.

## 10. Data and quality requirements

-   SQLite is the MVP persistent store.
-   FastAPI is the authoritative source for shipment state, readings,
    alerts, and assessments.
-   WebSocket updates are preferred for live readings and alerts;
    provide a documented polling fallback if WebSockets are unavailable.
-   Validate request payloads and profile limits.
-   Bound the reading generation rate and stop background tasks when a
    simulation ends.
-   Use stable IDs, UTC timestamps, and explicit units.
-   Do not put secrets in frontend source code.
-   Provide seeded demo data and a one-command local startup path where
    feasible.

## 11. Acceptance criteria

1.  The application starts using documented commands.
2.  A user can create and run a shipment without a hardware device.
3.  The 3D scene shows up to nine vial positions and independent sensor
    markers.
4.  All three views show the same shipment and alert state.
5.  A normal scenario produces no excursion alert while readings stay
    inside the configured range.
6.  Warming above the upper limit creates a persisted upper-limit alert.
7.  Cooling below the lower limit creates a persisted lower-limit alert.
8.  A sensor fault produces a sensor-health event and is not mislabelled
    as a temperature excursion by itself.
9.  Pause stops new readings; resume continues; end stops the
    simulation.
10. The operator can inspect the evidence and record a review.
11. The owner can see active alerts and shipment history.
12. A PDF report downloads and contains the simulation disclaimer.
13. The demo viability indicator shows its features/method and
    disclaimer.
14. Simulated NFC transfer has visible states and creates an audit
    event.
15. Refreshing the browser does not erase persisted shipment history.
16. No screen implies that the demo is a validated medical or regulatory
    decision system.

## 12. Demo success criteria

A judge can understand the system in under one minute, trigger an
excursion in under 15 seconds, see the alert propagate to another
dashboard, inspect why the system raised it, and download a report
without reloading or manually editing data.
