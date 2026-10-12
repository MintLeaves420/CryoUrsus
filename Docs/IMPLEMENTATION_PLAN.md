# CryoUrsus --- Implementation Plan

Build in this order. Do not attempt to implement all features in one
large prompt or patch.

## Phase 0 --- Inspect and baseline

-   [x] Inspect the repository and existing package/dependency versions.
-   [x] Confirm frontend and backend locations.
-   [x] Preserve working code; do not overwrite the starter app without
    understanding it.
-   [x] Add or update `.gitignore` and `.env.example`.
-   [x] Add a concise README with current run commands.
-   [x] Confirm frontend builds and backend starts before feature work.

**Exit check:** clean baseline with documented commands. (Completed - verified tests and build)

## Phase 1 --- Domain foundation

-   [x] Define product-profile, shipment, sensor, reading, alert,
    excursion, assessment, NFC transfer, and audit schemas.
-   [x] Initialize SQLite tables and indexes.
-   [x] Seed 2--3 clearly illustrative product profiles.
-   [x] Implement profile and shipment CRUD endpoints.
-   [x] Add health endpoint and API error shape.
-   [x] Add basic backend tests.

**Exit check:** can create a shipment, list it after a server restart,
and inspect its profile. (Completed - verified with automated tests)

## Phase 2 --- Truck simulator

-   [ ] Build responsive navigation and simulation indicator.
-   [ ] Build a basic 3D package/truck view.
-   [ ] Add 1--9 vial positions and independently positioned sensor
    markers.
-   [ ] Add product profile, vial count, sensor count, and scenario
    selection.
-   [ ] Add start, pause, resume, end controls.
-   [ ] Implement bounded simulation task lifecycle.
-   [ ] Store readings and expose a readings endpoint.
-   [ ] Build chart and readings table.

**Exit check:** normal scenario produces visible, persisted, timestamped
readings; pause/resume/end behave correctly.

## Phase 3 --- Excursions and alerts

-   [ ] Implement sensor-quality validation.
-   [ ] Implement upper/lower breach detection and event transitions.
-   [ ] Implement stuck/disconnected/implausible sensor scenarios.
-   [ ] Persist alerts and audit events.
-   [ ] Add WebSocket events and client reconnection snapshot.
-   [ ] Add polling fallback or visible disconnected state.
-   [ ] Add deterministic tests for upper/lower breaches and sensor
    faults.

**Exit check:** warming and cooling generate persisted alerts; sensor
faults are distinguished from temperature excursions.

## Phase 4 --- Demo viability and explanation

-   [ ] Implement feature extraction.
-   [ ] Implement a transparent, deterministic demo-only estimator.
-   [ ] Implement "Insufficient data" behavior.
-   [ ] Build explanation panel from actual feature values and rules.
-   [ ] Show method version and non-validation disclaimer.
-   [ ] Test same-input determinism and data-quality edge cases.

**Exit check:** estimate and explanation update with simulation events
without making real-world potency claims.

## Phase 5 --- Operator and Owner dashboards

-   [ ] Build shipment history and filters.
-   [ ] Show current status, latest readings, alert count, and sensor
    health.
-   [ ] Add shipment detail and event timeline.
-   [ ] Add operator assessment form.
-   [ ] Ensure both dashboards reflect backend state, not duplicated
    local mock data.
-   [ ] Add empty/loading/error states.

**Exit check:** an excursion triggered in Truck view appears in both
dashboards without manual refresh under normal WebSocket operation.

## Phase 6 --- NFC simulation and reports

-   [ ] Build simulated NFC scan/transfer states.
-   [ ] Persist transfer records and audit events.
-   [ ] Generate PDF from persisted shipment data.
-   [ ] Include readings summary, events, alerts, assessment, method
    version, and disclaimer.
-   [ ] Test empty/incomplete shipment report.

**Exit check:** transfer completes visibly and PDF downloads with the
correct shipment ID and simulation disclaimer.

## Phase 7 --- Presentation polish

-   [ ] Make normal, warming, cooling, and sensor-fault scenarios easy
    to trigger.
-   [ ] Improve 3D lighting, camera controls, and sensor selection only
    after core logic works.
-   [ ] Ensure charts/tables remain readable without 3D.
-   [ ] Add visible simulation labels and local timestamps.
-   [ ] Verify laptop presentation viewport.
-   [ ] Add a reset/demo-seed workflow with a deliberate confirmation.
-   [ ] Run backend tests, frontend tests, type check, and production
    build.
-   [ ] Update README with troubleshooting and demo script.

**Exit check:** all acceptance criteria in `PRD.md` pass.

## Recommended judge demo sequence (3--4 minutes)

1.  Create a shipment using an illustrative profile and 9 vials.
2.  Run the Normal scenario and show stable readings.
3.  Trigger Gradual Warming; show the reading chart cross the upper
    configured limit.
4.  Switch to Operator Dashboard and show the alert, event duration,
    explanation, and review action.
5.  Switch to Owner Dashboard and show the same alert and shipment
    status.
6.  Trigger a sensor fault in a separate shipment and show data-quality
    handling.
7.  Run the simulated NFC transfer and download a PDF report.
8.  Explicitly state that the viability estimate and profile are
    illustrative demo outputs, not validated product-release guidance.

## Agent task template

For each phase, ask the coding agent to: 1. Read the relevant project
docs and inspect current files. 2. State the files it plans to change
and why. 3. Implement only the requested phase. 4. Run tests/build
checks. 5. Summarize files changed, commands run, outcomes, and
remaining issues. 6. Update this checklist only for work actually
verified.
