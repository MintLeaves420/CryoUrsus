# Agent Rules --- CryoUrsus

These instructions apply to every coding agent working in this
repository. Follow them before making changes.

## 1. Product truth and safety

-   This is a hackathon simulation, not a validated cold-chain device or
    medical decision system.
-   Label simulated readings, demo predictions, sample profiles, and
    reports as simulated.
-   Never claim real potency, remaining shelf life, regulatory
    compliance, or validated viability.
-   Never invent official product limits. Profile values must be
    explicitly marked illustrative unless supported by a verified,
    product-specific source.
-   A demo score must not be presented as permission to release or
    reject real biologics.
-   Keep "technical status", "demo viability estimate", and "human
    review status" distinct.

## 2. Architecture boundaries

-   Frontend: React + TypeScript + Vite.
-   3D: Three.js through React Three Fiber and Drei if useful.
-   Backend: Python + FastAPI.
-   Persistence: SQLite for MVP.
-   Charts: Recharts or another already-installed chart library; do not
    add a second charting library without a clear reason.
-   Keep API access in a frontend service layer, not scattered direct
    fetch calls.
-   Keep business logic on the backend. Frontend may animate and render,
    but must not be the source of truth for shipment, excursion, alert,
    or assessment records.
-   Separate simulation generation, sensor validation, excursion
    detection, demo viability, explanation, alerting, persistence, and
    reporting into distinct modules.
-   Do not add microservices, Redis, Docker orchestration, or a complex
    cloud architecture unless explicitly requested.

## 3. Antigravity workflow and shared-file safety

-   Read `PRD.md`, `software-architecture.md`, `data-model.md`, and
    `API.md` before implementation.
-   Read `IMPLEMENTATION_PLAN.md` and update it as tasks are completed.
-   Work in small, testable increments. Build and verify the foundation
    before adding features.
-   Before editing a shared file, inspect its current contents and
    related imports.
-   Do not have multiple agents edit the same file concurrently. Assign
    clear file ownership or serialize the edits.
-   Do not overwrite working code with a wholesale rewrite when a
    focused change is sufficient.
-   After a change, run the relevant tests, type checks, lint/build
    commands available in the repository, and report failures honestly.
-   If a requirement is ambiguous, prefer the smallest implementation
    that satisfies the PRD and document the assumption.
-   Do not silently remove an existing feature to make a new feature
    easier.

## 4. Code quality

-   Use TypeScript strict mode where practical. Avoid `any`; explain
    unavoidable exceptions.
-   Use Pydantic models for API request/response validation.
-   Use typed domain models and enums for statuses and event types.
-   Keep functions small and name them after their purpose.
-   Avoid duplicated threshold logic; implement one authoritative
    excursion engine.
-   Avoid magic numbers. Put simulation intervals, profile limits, and
    demo-model parameters in configuration/profile data.
-   Use UTC timestamps in storage and ISO 8601 in APIs.
-   Every temperature value must include or inherit an explicit unit;
    use °C consistently in the MVP.
-   Handle empty data, API failure, disconnected WebSocket, and missing
    profile states.
-   Do not swallow exceptions. Log useful error context without secrets
    or personal data.
-   Avoid decorative UI elements that imply real sensors or live network
    connectivity when the data are simulated.

## 5. Simulation lifecycle

-   Only one active simulation task per shipment.
-   Starting an already-running simulation must not create duplicate
    loops.
-   Pausing must stop generation without ending the shipment.
-   Resuming must not create duplicate tasks.
-   Ending must cancel/stop the task and persist final status.
-   Disconnecting a browser must not create an uncontrolled runaway
    simulation. Define backend task cleanup and document the behavior.
-   Use a configurable tick interval; do not generate unbounded readings
    or flood the UI.
-   Sensor faults must be represented as sensor health states and
    events, not merely as extreme temperatures.
-   A stuck sensor should have a clear detection rule, such as unchanged
    values across a configurable number of consecutive samples, and the
    rule should be documented.

## 6. Excursion and alert rules

-   Evaluate only valid readings for temperature excursion logic.
-   A reading below the lower limit or above the upper limit is a
    breach; equality is within range unless the profile explicitly says
    otherwise.
-   Treat sensor faults and temperature excursions as different event
    types.
-   Record transitions into and out of a breach. Do not create one alert
    per sample during a continuous breach.
-   If sensor data are invalid or stale, surface data-quality status
    rather than asserting the shipment is safe.
-   Any status calculation must be deterministic and unit tested.
-   Alerts are persisted before they are broadcast to connected clients.

## 7. Demo viability and explainability

-   The demo predictor must be deterministic for the same input features
    and version.
-   Prefer a transparent formula or simple interpretable model over an
    opaque model.
-   Do not call the score "actual viability" or "potency".
-   Include the features used, the model/method version, and a
    plain-language explanation.
-   Return "Insufficient data" when there is not enough trustworthy
    data.
-   The explanation must reflect the actual calculation; do not generate
    fictional post-hoc reasons.
-   Tests must cover normal, warming, cooling, and sensor-fault
    conditions.

## 8. API and persistence

-   Use Pydantic schemas at API boundaries.
-   Return clear HTTP status codes and structured error messages.
-   Persist all key state transitions and audit events.
-   Use SQLite foreign keys where applicable and create tables through a
    migration or startup initialization path.
-   Do not store secrets in the database unless necessary; never commit
    credentials.
-   Provide CORS only for the local frontend origin(s) required for
    development.
-   WebSocket messages should have a versioned or clearly typed event
    shape.
-   If WebSocket updates fail, the UI should show stale/disconnected
    status and use polling fallback if implemented.

## 9. UI and accessibility

-   Every chart includes a title, axis labels, units, and a useful empty
    state.
-   Never rely on color alone to communicate a breach or fault.
-   Keep alert text concise and actionable.
-   Make loading, error, empty, paused, completed, and disconnected
    states visible.
-   3D interactions must not block access to readings in a table or
    chart.
-   Provide keyboard-accessible controls and descriptive button labels.
-   Use responsive layouts suitable for a laptop presentation.
-   Do not add animation that obscures critical information.

## 10. Testing and definition of done

A task is done only when: - The behavior matches the PRD and
architecture. - Relevant unit/integration tests pass, or any missing
tests are explicitly noted. - The frontend builds and the backend
starts. - API and UI error states are handled. - No debug secrets, fake
claims, or unexplained placeholder values remain. - Documentation is
updated when behavior, endpoints, schema, or setup changes. - A concise
change summary and verification results are provided.

## 11. Dependency discipline

-   Inspect existing dependencies before adding packages.
-   Add only dependencies needed for a defined requirement.
-   Pin or constrain versions using the project's package-management
    convention.
-   Do not switch frameworks or replace libraries without explicit
    approval.
-   Avoid external network dependencies for core demo flows.

## 12. Git hygiene

-   Make small logical commits if Git is being used.
-   Do not commit `.env`, secrets, local databases containing personal
    data, build output, or virtual environments.
-   Maintain `.env.example` with safe placeholder values.
-   Keep README setup instructions accurate.
